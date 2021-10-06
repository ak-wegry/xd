# coding: shift_jis 
# =============================================================================
# �t�@�C����16�i���\��
# =============================================================================
# [�ύX����]
# Ver0.00  2021/05/22 �쐬�J�n
# Ver1.00  2021/05/29 �V�K�쐬

usage = """
xd.py - �t�@�C����16�i���\��  [Ver1.00  2021/5/29]

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
	�l���w��͈͓��ɂ��邩�̃`�F�b�N

	Args:
		chk_val int:
			�`�F�b�N�Ώۂ̒l
		range_list list:
			�w��͈�(chk_val=p1�`p2 [or chk_val=p3�`p4...])
	Returns:
		boolean:
			TRUE  �w��͈͓�
			FALSE �w��͈͊O
	"""
	stat = False
	for n in list(range(0, len(range_list), 2)):
		if range_list[n] <= chk_val and chk_val <= range_list[n+1]:
			stat = True
			break
	return stat

def get_dsp_txt(bin, start, byte_max, in_enc):
	"""
	���͕�������w��o�C�g���ȓ��̕���������o��

	Args:
		txt str:
			���͕�����
		start int:
			�Q�ƊJ�n�����ʒu
		byte_max int:
			���o���ő�o�C�g��
		in_enc str:
			���͕�����̊����R�[�h
	Returns:
		list:
			���o����������
			���o�����o�C�g��
	"""

	# JIS�̑O��ŏIESC�V�[�P���X��ۑ�
	add_esc  = get_dsp_txt.jis_esc

	# UTF�n�t�@�C���̃o�C�g���}�[�N(BOM)�Ɋւ�����ݒ�
	ctrl_dot = "."	# ����R�[�h��\���p�ɕϊ����镶��
	head_dot = ""	# �t�@�C���擪�̃o�C�g���}�[�N�\��
	add_bom  = b""	# ������������f�R�[�h���鎞�ɕt������o�C�g���}�[�N
	esc_flg = False	# JIS ESC�V�[�P���X�̒~�ϕ\��

	if in_enc == "UTF-8-SIG" and start == 0:
		head_dot = "..."
	elif in_enc == "UTF-16":
		ctrl_dot = ".."
		if start == 0:
			head_dot = ".."
		else:
			add_bom = bin[0:2]

	# ����/����R�[�h�̋�؂���l�������f�[�^�؏o���ʒu����
	byte_cnt = 0	# �ő�o�C�g���ȓ��ŁA�؏o�������o�C�g��
	rest_cnt = 0	# �}���`�o�C�g��2�o�C�g�ڈȍ~�̓ǂݔ�΂���
	other_f = False	# �G���R�[�h�s���\��
	dot_pos = []	# ����R�[�h�̓��͕�������ʒu(�G���R�[�h�s����)
	for c in bin[start:]:
		if byte_cnt < byte_max:
			if rest_cnt > 0:
				rest_cnt -= 1
				if esc_flg:
					get_dsp_txt.jis_esc += bytes([c]) # ()���̒l��[]�ň͂�
					if rest_cnt == 0:
						esc_flg = False
			else:
				add_cnt = 1	# �؏o���o�C�g��
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
						get_dsp_txt.jis_esc = bytes([c]) # ()���̒l��[]�ň͂�
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

	# �؏o���ʒu�̃f�[�^���f�R�[�h/����R�[�h��"."�ϊ����āA�\��������𐶐�
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
get_dsp_txt.jis_esc = b""	# JIS��ESC�V�[�P���X(�ÓI�ϐ�)������

#--- main ----------------------------------------------------------------------
## �����`�F�b�N
if len(sys.argv) == 2:
	# �t�@�C������̓���
	file_name = sys.argv[1]
	with open(file_name, "rb") as f:
		txt = f.read()
else:
	if sys.stdin.isatty():
		print(usage)
		sys.exit(0)
	else:
		# stdin����̓���
		file_name = sys.stdin
		txt = bytes(file_name.read(), file_name.encoding)

## ���͕�����̃G���R�[�f�B���O����
def_enc = locale.getpreferredencoding()
guess = chardet.detect(txt).get("encoding")
if guess is None:
	guess = locale.getpreferredencoding()
elif guess == "ISO-2022-JP":
	# JIS7����̓��ꏈ��
	guess = "ISO-2022-JP-EXT"
elif guess == "ISO-8859-1" or guess == "KOI8-R":
	# JIS8->JIS7�ϊ�(���ꏈ��)
	cnv_txt = bytearray(txt)
	for i, ascii in enumerate(cnv_txt):
		if ascii >= 0xa1 and ascii <= 0xdf:
			cnv_txt[i] = ascii - 0x80
	txt = bytes(cnv_txt)
	guess = "ISO-2022-JP-EXT"

## 16�i���\��
address = 0		# 16�i���\��������͕�����̐擪����̃o�C�g�ʒu
start_pos = 0	# �o�C�i���������ϊ��̃f�[�^�Q�ƊJ�n�ʒu
max_byte = 16	# 1�s���ɕ\������Q�ƃf�[�^�̍ő�o�C�g��

for c in txt:
	# �A�h���X�\��
	if address % 16 == 0:
		print(f"{address:08x}  ", end="")

	# 1������16�i���\��
	print(f"{c:02x} ", end="")

	# 8�������̋�؂�
	if address % 16 == 7:
		print(" ", end="")

	# 16�������̉��s
	if address % 16 == 15:
		ret_list = get_dsp_txt(txt, start_pos, max_byte, guess)
		dsp_txt = ret_list[0]
		txt_byte = int(ret_list[1])
		start_pos += txt_byte
		max_byte = address + 1 + 16 - start_pos
		print(f"  {dsp_txt}")

	# �A�h���X�X�V
	address += 1

# 16�����ɖ����Ȃ��Ō�̕������o��
end_pos = address % 16
if end_pos != 0:
	for i in range(end_pos, 16):
		print("   ", end="")
	if end_pos < 8:
		print(" ", end="")

	ret_list = get_dsp_txt(txt, start_pos, max_byte, guess)
	dsp_txt = ret_list[0]
	print(f"  {dsp_txt}")
