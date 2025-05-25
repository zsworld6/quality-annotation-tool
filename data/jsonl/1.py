#!/usr/bin/env python3
"""
快速移除JSONL文件中的ori_html字段
使用方法: python quick_remove_ori_html.py
"""

import json
import os
import shutil

def quick_remove_ori_html():
    """快速处理当前目录下的三个文件"""
    
    files_to_process = [
        "test_set_unmatched_part1.jsonl",
        "test_set_unmatched_part2.jsonl", 
        "test_set_unmatched_part3.jsonl"
    ]
    
    for filename in files_to_process:
        if not os.path.exists(filename):
            print(f"⚠️  文件不存在: {filename}")
            continue
            
        print(f"🔄 处理文件: {filename}")
        
        # 获取原始大小
        original_size = os.path.getsize(filename)
        print(f"   原始大小: {original_size / (1024*1024):.2f} MB")
        
        # 创建备份
        backup_name = f"{filename}.backup"
        if not os.path.exists(backup_name):
            shutil.copy2(filename, backup_name)
            print(f"   ✅ 已创建备份: {backup_name}")
        
        # 处理文件
        temp_name = f"{filename}.temp"
        processed_lines = 0
        
        try:
            with open(filename, 'r', encoding='utf-8') as f_in, \
                 open(temp_name, 'w', encoding='utf-8') as f_out:
                
                for line_num, line in enumerate(f_in, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # 移除ori_html字段
                        if 'ori_html' in data:
                            del data['ori_html']
                            processed_lines += 1
                        
                        f_out.write(json.dumps(data, ensure_ascii=False) + '\n')
                        
                    except json.JSONDecodeError:
                        # 跳过无法解析的行
                        continue
            
            # 替换原文件
            os.replace(temp_name, filename)
            
            # 获取新大小
            new_size = os.path.getsize(filename)
            saved_mb = (original_size - new_size) / (1024*1024)
            saved_percent = (original_size - new_size) / original_size * 100
            
            print(f"   ✅ 处理完成!")
            print(f"   新文件大小: {new_size / (1024*1024):.2f} MB")
            print(f"   节省空间: {saved_mb:.2f} MB ({saved_percent:.1f}%)")
            print(f"   处理行数: {processed_lines}")
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            if os.path.exists(temp_name):
                os.remove(temp_name)
        
        print()

if __name__ == "__main__":
    print("🚀 快速移除ori_html字段工具")
    print("=" * 40)
    quick_remove_ori_html()
    print("🎉 所有文件处理完成!")