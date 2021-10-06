# coding: shift_jis 
# =============================================================================
# ファイルの16進数表示
# =============================================================================
# [変更履歴]
# Ver0.00  2021/05/22 作成開始
# Ver1.00  2021/05/29 新規作成

usage = """
xd.py - ファイルの16進数表示  [Ver1.00  2021/5/29]

Usage : xd.py filename
"""

import os
import sys
import pathlib
import math
import chardet
import locale
import re

def chk_range(chk_val, range_list):
	"""
	値が指定範囲内にあるかのチェック

	Args:
		chk_val int:
			チェック対象の値
		range_list list:
			指定範囲(chk_val=p1～p2 [or chk_val=p3～p4...])
	Returns:
		boolean:
			TRUE  指定範囲内
			FALSE 指定範囲外
	"""
	stat = False
	for n in list(range(0, len(range_list), 2)):
		if range_list[n] <= chk_val and chk_val <= range_list[n+1]:
			stat = True
			break
	return stat

def get_dsp_txt(bin, start, byte_max, in_enc):
	"""
	入力文字から指定バイト数以内の文字列を取り出す

	Args:
		txt str:
			入力文字列
		start int:
			参照開始文字位置
		byte_max int:
			取り出す最大バイト数
		in_enc str:
			入力文字列の漢字コード
	Returns:
		list:
			取り出した文字列
			取り出したバイト数
	"""

	# JISの前回最終ESCシーケンスを保存
	add_esc  = get_dsp_txt.jis_esc

	# UTF系ファイルのバイト順マーク(BOM)に関する情報設定
	ctrl_dot = "."	# 制御コードを表示用に変換する文字
	head_dot = ""	# ファイル先頭のバイト順マーク表示
	add_bom  = b""	# 部分文字列をデコードする時に付加するバイト順マーク
	esc_flg = False	# JIS ESCシーケンスの蓄積表示

	if in_enc == "UTF-8-SIG" and start == 0:
		head_dot = "..."
	elif in_enc == "UTF-16":
		ctrl_dot = ".."
		if start == 0:
			head_dot = ".."
		else:
			add_bom = bin[0:2]

	# 漢字/制御コードの区切りを考慮したデータ切出し位置判定
	byte_cnt = 0	# 最大バイト数以内で、切出した総バイト数
	rest_cnt = 0	# マルチバイトで2バイト目以降の読み飛ばす数
	other_f = False	# エンコード不明表示
	dot_pos = []	# 制御コードの入力文字列内位置(エンコード不明時)
	for c in bin[start:]:
		if byte_cnt < byte_max:
			if rest_cnt > 0:
				rest_cnt -= 1
				if esc_flg:
					get_dsp_txt.jis_esc += bytes([c]) # ()内の値は[]で囲む
					if rest_cnt == 0:
						esc_flg = False
			else:
				add_cnt = 1	# 切出すバイト数
				if in_enc == "SHIFT_JIS":
					if chk_range(c, [0x81, 0x9f, 0xe0, 0xfc]):
						add_cnt = 2
				elif in_enc == "EUC-JP":
					if chk_range(c, [0xa1, 0xfe, 0x8e, 0x8e]):
						add_cnt = 2
				elif in_enc == "utf-8" or in_enc == "UTF-8-SIG":
					if chk_range(c, [0xc2, 0xdf]):
						add_cnt = 2
					elif chk_range(c, [0xe0, 0xef]):
						add_cnt = 3
					elif chk_range(c, [0xf0, 0xf7]):
						add_cnt = 4
				elif in_enc == "UTF-16":
					add_cnt = 2
				elif in_enc == "ISO-2022-JP-EXT":
					if c == 0x1b:
						add_cnt = 3
						esc_flg = True
						get_dsp_txt.jis_esc = bytes([c]) # ()内の値は[]で囲む
					elif get_dsp_txt.jis_esc == b"\x1b\x24\x40" or \
					     get_dsp_txt.jis_esc == b"\x1b\x24\x42":
						add_cnt = 2
				else:
					other_f = True
					if chk_range(c, [0x20, 0x7e]) == False:
						dot_pos.append(byte_cnt)

				byte_cnt += add_cnt
				rest_cnt = add_cnt - 1
		else:
			break

	# 切出し位置のデータをデコード/制御コードを"."変換して、表示文字列を生成
	end = start + byte_cnt
	if other_f:
		ext_txt = bin[start:end]
		for n in dot_pos:
			ext_txt = ext_txt[0:n] + b"." + ext_txt[n+1:]
		ext_txt = ext_txt.decode(in_enc)
	else:
		if add_esc == b"":
			add_esc = get_dsp_txt.jis_esc
		ext_txt = (add_bom + add_esc + bin[start:end]).decode(in_enc)
		ext_txt = re.sub(r"[\u0000-\u001f]", ctrl_dot, ext_txt)
		ext_txt = head_dot + ext_txt

	return [ext_txt, str(byte_cnt)]
get_dsp_txt.jis_esc = b""	# JISのESCシーケンス(静的変数)初期化

#--- main ----------------------------------------------------------------------
## 引数チェック
if len(sys.argv) == 2:
	# ファイルからの入力
	file_name = sys.argv[1]
	with open(file_name, "rb") as f:
		txt = f.read()
else:
	if sys.stdin.isatty():
		print(usage)
		sys.exit(0)
	else:
		# stdinからの入力
		file_name = sys.stdin
		txt = bytes(file_name.read(), file_name.encoding)

## 入力文字列のエンコーディング判定
def_enc = locale.getpreferredencoding()
guess = chardet.detect(txt).get("encoding")
if guess is None:
	guess = locale.getpreferredencoding()
elif guess == "ISO-2022-JP":
	# JIS7限定の特殊処理
	guess = "ISO-2022-JP-EXT"
elif guess == "ISO-8859-1" or guess == "KOI8-R":
	# JIS8->JIS7変換(特殊処理)
	cnv_txt = bytearray(txt)
	for i, ascii in enumerate(cnv_txt):
		if ascii >= 0xa1 and ascii <= 0xdf:
			cnv_txt[i] = ascii - 0x80
	txt = bytes(cnv_txt)
	guess = "ISO-2022-JP-EXT"

## 16進数表示
address = 0		# 16進数表示する入力文字列の先頭からのバイト位置
start_pos = 0	# バイナリ→文字変換のデータ参照開始位置
max_byte = 16	# 1行内に表示する参照データの最大バイト数

for c in txt:
	# アドレス表示
	if address % 16 == 0:
		print(f"{address:08x}  ", end="")

	# 1文字の16進数表示
	print(f"{c:02x} ", end="")

	# 8文字毎の区切り
	if address % 16 == 7:
		print(" ", end="")

	# 16文字毎の改行
	if address % 16 == 15:
		ret_list = get_dsp_txt(txt, start_pos, max_byte, guess)
		dsp_txt = ret_list[0]
		txt_byte = int(ret_list[1])
		start_pos += txt_byte
		max_byte = address + 1 + 16 - start_pos
		print(f"  {dsp_txt}")

	# アドレス更新
	address += 1

# 16文字に満たない最後の文字を出力
end_pos = address % 16
if end_pos != 0:
	for i in range(end_pos, 16):
		print("   ", end="")
	if end_pos < 8:
		print(" ", end="")

	ret_list = get_dsp_txt(txt, start_pos, max_byte, guess)
	dsp_txt = ret_list[0]
	print(f"  {dsp_txt}")
