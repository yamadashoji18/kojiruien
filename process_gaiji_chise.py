#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
import os
from urllib.parse import urlparse, unquote
from datetime import datetime

def extract_unicode_from_url(url):
    """
    CHISE URLの末尾にある%XXバイト列または0x形式からUnicodeコードポイントを抽出
    """
    try:
        # URLの末尾部分（最後の/以降）を取得
        url_parts = url.rstrip('/').split('/')
        if not url_parts:
            return None
        
        last_part = url_parts[-1]
        print(f"    URL末尾部分: {last_part}")
        
        # URL末尾から0x形式のコードポイントをチェック
        hex_match = re.search(r'0x([0-9A-Fa-f]+)', last_part)
        if hex_match:
            hex_value = hex_match.group(1)
            try:
                code_point = int(hex_value, 16)
                unicode_code = f"U+{code_point:04X}"
                print(f"    0x形式から抽出されたUnicodeコードポイント: {unicode_code} (0x{hex_value})")
                return unicode_code
            except ValueError as e:
                print(f"    0x形式の16進数変換エラー: {e}")
        
        # %XXバイト列が含まれているかチェック
        if '%' not in last_part:
            print("    %XXバイト列や0x形式が見つかりません")
            return None
        
        # URLデコードしてバイト列を文字に変換
        try:
            decoded_str = unquote(last_part)
            print(f"    デコード結果: {repr(decoded_str)}")
            
            # 文字をUnicodeコードポイントに変換
            if len(decoded_str) > 0:
                # 最初の文字のコードポイントを取得
                first_char = decoded_str[0]
                code_point = ord(first_char)
                unicode_code = f"U+{code_point:04X}"
                print(f"    抽出されたUnicodeコードポイント: {unicode_code} (文字: '{first_char}')")
                return unicode_code
            else:
                print("    デコード後の文字列が空です")
                return None
                
        except Exception as e:
            print(f"    URLデコードエラー: {e}")
            
            # 手動で%XXを解析してみる
            percent_parts = last_part.split('%')[1:]  # %以降の部分
            if percent_parts:
                try:
                    # %XXバイト列をバイト配列に変換
                    byte_values = []
                    for part in percent_parts:
                        if len(part) >= 2:
                            hex_value = part[:2]
                            byte_values.append(int(hex_value, 16))
                    
                    if byte_values:
                        # バイト配列をUTF-8として解釈
                        byte_array = bytes(byte_values)
                        utf8_str = byte_array.decode('utf-8')
                        if len(utf8_str) > 0:
                            first_char = utf8_str[0]
                            code_point = ord(first_char)
                            unicode_code = f"U+{code_point:04X}"
                            print(f"    手動解析でUnicodeコードポイント抽出: {unicode_code} (文字: '{first_char}')")
                            return unicode_code
                except Exception as e2:
                    print(f"    手動解析もエラー: {e2}")
            
            return None
            
    except Exception as e:
        print(f"    URL解析エラー: {e}")
        return None

def main():
    """
    gaiji_chise.xlsxファイルを処理するメイン関数
    """
    try:
        # Excelファイルを読み込む
        print("Excelファイルを読み込み中...")
        df = pd.read_excel('gaiji_chise.xlsx')
        print(f"✓ Excelファイルを正常に読み込みました（{df.shape[0]}行, {df.shape[1]}列）")
        
        # カラム名を表示
        print("\nカラム名:")
        for i, col in enumerate(df.columns):
            print(f"  {chr(65+i)}: {col}")
        
        # フォントカラムの確認（文字化けチェック）
        font_columns = [col for col in df.columns if 'フォント' in str(col) or 'font' in str(col).lower()]
        print(f"\nフォントカラム: {font_columns}")
        
        # 文字化けしているかチェック
        font_corrupted = False
        if font_columns:
            font_col = font_columns[0]
            sample_values = df[font_col].dropna().head(5).astype(str)
            print(f"フォントカラムのサンプル値: {list(sample_values)}")
            
            # 文字化けの判定（U+20000以上のコードポイントが含まれているかチェック）
            for val in sample_values:
                try:
                    for char in val:
                        if ord(char) >= 0x20000:  # U+20000以上の文字（拡張漢字領域等）
                            print(f"  ⚠ 文字化けの可能性を検出: '{val}' (文字: '{char}', コード: U+{ord(char):04X})")
                            font_corrupted = True
                            break
                    if font_corrupted:
                        break
                except Exception as e:
                    print(f"  ❌ 文字化けチェック中にエラー: {val} -> {e}")
                    continue
            
            # 判定結果を表示
            if font_corrupted:
                print("📋 文字化け判定結果: 文字化けが検出されました（U+20000以上の文字が含まれています）")
            else:
                print("📋 文字化け判定結果: 正常です（U+20000以上の文字は検出されませんでした）")
        
        # CHISE URLカラムを見つける
        url_columns = [col for col in df.columns if 'CHISE' in str(col) or 'URL' in str(col)]
        print(f"CHISE URLカラム: {url_columns}")
        
        if not url_columns:
            print("❌ CHISE URLカラムが見つかりません")
            return
        
        url_col = url_columns[0]
        
        # Fカラム（CHISE URLの%XXバイト列または0x形式から変換したUnicodeコードポイント用）を新しく作成
        f_col = 'ユニコードコードポイント'
        if f_col not in df.columns:
            df[f_col] = ''  # 空の列を追加
            print(f"✓ 新しいFカラムを作成しました: {f_col}")
        else:
            print(f"Fカラムは既に存在します: {f_col}")
        
        # フォントカラムが文字化けしている場合、またはユーザーが処理を希望する場合
        if font_corrupted or True:  # 常に処理を実行
            print("\n🔄 CHISE URLの%XXバイト列または0x形式からUnicodeコードポイントを抽出して処理を開始します...")
            
            # URLが存在する行を処理
            url_rows = df[df[url_col].notna() & (df[url_col] != '')]
            print(f"処理対象のURL数: {len(url_rows)}")
            
            processed_count = 0
            for idx, row in url_rows.iterrows():
                url = row[url_col]
                if pd.isna(url) or url == '':
                    continue
                
                print(f"\n処理中 ({processed_count + 1}/{len(url_rows)}): {url}")
                
                try:
                    # URL末尾の%XXバイト列または0x形式からUnicodeコードポイントを抽出
                    unicode_code = extract_unicode_from_url(url)
                    
                    if unicode_code:
                        df.at[idx, f_col] = unicode_code
                        print(f"  ✓ URLから抽出したUnicodeコードポイントをFカラムに格納: {unicode_code}")
                        processed_count += 1
                    else:
                        print("  ⚠ URLからUnicodeコードポイントを抽出できませんでした（解析エラー）")
                        
                except Exception as e:
                    print(f"  ❌ URL解析エラー: {e}")
            
            print(f"\n✓ 処理完了: {processed_count}件のUnicodeコードポイントをURLの%XXバイト列または0x形式から抽出してFカラムに格納しました")
        
        # 更新されたExcelファイルを別名で保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"gaiji_chise_updated_{timestamp}.xlsx"
        df.to_excel(output_filename, index=False)
        print(f"\n✓ 更新されたファイルを保存しました: {output_filename}")
        
        # 結果の概要を表示
        updated_count = df[f_col].notna().sum()
        non_empty_count = (df[f_col] != '').sum()
        print(f"Fカラム（{f_col}）に値が設定された行数: {non_empty_count}")
        
        # Fカラムの値のサンプルを表示
        sample_f_values = df[df[f_col] != ''][f_col].head(10)
        if len(sample_f_values) > 0:
            print("Fカラムの値のサンプル:")
            for val in sample_f_values:
                print(f"  {val}")
        
    except FileNotFoundError:
        print("❌ gaiji_chise.xlsx ファイルが見つかりません")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

