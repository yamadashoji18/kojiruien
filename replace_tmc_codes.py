#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
import os
from datetime import datetime

def main():
    """
    TMCコードをフォントで置き換えるメイン関数
    """
    try:
        print("=== TMCコード置換スクリプト ===\n")
        
        # 1. gaiji_chise.xlsからファイル名、フォント、コードポイントを読み込む
        print("1. Excelファイルを読み込み中...")
        excel_file = 'gaiji_chise.xlsx'
        if not os.path.exists(excel_file):
            print(f"❌ {excel_file} ファイルが見つかりません")
            return
        
        df = pd.read_excel(excel_file)
        print(f"✓ Excelファイルを正常に読み込みました（{df.shape[0]}行, {df.shape[1]}列）")
        
        # カラム名を表示
        print("\nカラム名:")
        for i, col in enumerate(df.columns):
            print(f"  {chr(65+i)}: {col}")
        
        # 必要なカラムを特定
        filename_columns = [col for col in df.columns if 'ファイル' in str(col) or 'file' in str(col).lower()]
        font_columns = [col for col in df.columns if 'フォント' in str(col) or 'font' in str(col).lower()]
        
        if not filename_columns:
            print("❌ ファイル名カラムが見つかりません")
            return
        if not font_columns:
            print("❌ フォントカラムが見つかりません")
            return
        
        filename_col = filename_columns[0]
        font_col = font_columns[0]
        
        print(f"ファイル名カラム: {filename_col}")
        print(f"フォントカラム: {font_col}")
        
        # データを辞書形式で準備（ファイル名から拡張子を除いた部分をキーとする）
        font_mapping = {}
        for idx, row in df.iterrows():
            filename = row[filename_col]
            font = row[font_col]
            
            if pd.notna(filename) and pd.notna(font) and str(font).strip():
                # ファイル名から拡張子を除く
                basename = os.path.splitext(str(filename))[0]
                font_mapping[basename] = str(font).strip()
        
        print(f"✓ {len(font_mapping)}件のフォントマッピングを準備しました")
        
        # マッピングのサンプルを表示
        if font_mapping:
            print("フォントマッピングのサンプル:")
            sample_items = list(font_mapping.items())[:5]
            for basename, font in sample_items:
                print(f"  {basename} → {font}")
        
        # 2. SYOKOBUTUBU-1.txtをUTF-16で読み込む
        print(f"\n2. ファイルをUTF-16で読み込み中...")
        # ../識別_外字統合後/にあるすべてのtxtファイルを処理
        txt_dir = '../識別_外字統合後/'
        if not os.path.exists(txt_dir):
            print(f"❌ ディレクトリ {txt_dir} が見つかりません")
            return
        
        txt_files = [f for f in os.listdir(txt_dir) if f.endswith('.txt')]
        if not txt_files:
            print(f"❌ {txt_dir} にtxtファイルが見つかりません")
            return
        
        print(f"✓ {len(txt_files)}個のtxtファイルを発見しました: {txt_files}")
        
        for txt_filename in txt_files:
            txt_file = os.path.join(txt_dir, txt_filename)
            print(f"\n--- {txt_filename} の処理を開始 ---")
            
            if not os.path.exists(txt_file):
                print(f"❌ {txt_file} ファイルが見つかりません")
                continue
        
            try:
                with open(txt_file, 'r', encoding='utf-16') as f:
                    content = f.read()
                print(f"✓ {txt_file} を正常に読み込みました（{len(content)}文字）")
            except UnicodeError:
                # UTF-16で読み込めない場合は他のエンコーディングを試す
                print("UTF-16での読み込みに失敗しました。他のエンコーディングを試行中...")
                for encoding in ['utf-16le', 'utf-16be', 'utf-8', 'shift_jis']:
                    try:
                        with open(txt_file, 'r', encoding=encoding) as f:
                            content = f.read()
                        print(f"✓ {txt_file} を{encoding}で読み込みました（{len(content)}文字）")
                        break
                    except UnicodeError:
                        continue
                else:
                    print(f"❌ {txt_file} を読み込めませんでした")
                    continue
        
            # 3. TMCコードの置換処理
            print(f"\n3. TMCコードの置換処理を開始...")
            
            # <tmc code="xxxx"/>パターンを検索
            tmc_pattern = r'<tmc code="([^"]+)"/>'
            tmc_matches = re.findall(tmc_pattern, content)
            
            print(f"TMCコードを{len(tmc_matches)}個発見しました")
            
            if tmc_matches:
                print("発見されたTMCコードのサンプル:")
                sample_codes = tmc_matches[:10]
                for code in sample_codes:
                    print(f"  {code}")
            
            # 置換処理
            replacement_count = 0
            modified_content = content
            
            def replace_tmc(match):
                nonlocal replacement_count
                code = match.group(1)
                
                # コードがフォントマッピングに存在し、フォントが空でない場合
                if code in font_mapping:
                    font = font_mapping[code]
                    replacement_count += 1
                    print(f"  置換: <tmc code=\"{code}\"/> → {font}")
                    return font
                else:
                    # 一致しない場合はそのまま
                    return match.group(0)
            
            # 全てのTMCコードを処理
            modified_content = re.sub(tmc_pattern, replace_tmc, modified_content)
            
            print(f"\n✓ {replacement_count}件のTMCコードを置換しました")
        
            # 4. 結果を新しいファイルに保存
            base_name = os.path.splitext(os.path.basename(txt_file))[0]
            output_file = f"replaced_{base_name}.txt"
        
            # 元のエンコーディングで保存（UTF-16を試し、失敗したらUTF-8）
            try:
                with open(output_file, 'w', encoding='utf-16') as f:
                    f.write(modified_content)
                print(f"✓ 置換結果をUTF-16で保存しました: {output_file}")
            except UnicodeError:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                print(f"✓ 置換結果をUTF-8で保存しました: {output_file}")
            
            # 5. ファイル別処理結果のサマリー
            print(f"\n=== {txt_filename} 処理結果 ===")
            print(f"発見されたTMCコード: {len(tmc_matches)}件")
            print(f"置換されたTMCコード: {replacement_count}件")
            print(f"出力ファイル: {output_file}")
            
            # 置換されなかったTMCコードがあれば表示
            unreplaced_codes = set(tmc_matches) - set(font_mapping.keys())
            if unreplaced_codes:
                print(f"\n置換されなかったTMCコード（{len(unreplaced_codes)}件）:")
                sample_unreplaced = list(unreplaced_codes)[:10]
                for code in sample_unreplaced:
                    print(f"  {code}")
                if len(unreplaced_codes) > 10:
                    print(f"  ... 他{len(unreplaced_codes) - 10}件")
        
        # 6. 全体の処理結果サマリー
        print(f"\n=== 全体処理結果サマリー ===")
        print(f"読み込んだフォントマッピング: {len(font_mapping)}件")
        print(f"処理したファイル数: {len(txt_files)}件")
        print(f"処理したファイル: {', '.join(txt_files)}")
        
    except FileNotFoundError as e:
        print(f"❌ ファイルが見つかりません: {e}")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
