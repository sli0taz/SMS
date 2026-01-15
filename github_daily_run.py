#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 专用每日运行脚本 - 智能对话版
特点：
- 无头浏览器模式（服务器适配）
- 集成 DrissionPage 高效底层
- 包含滑块检测与跳过
- 4轮拟人化智能对话逻辑
- 自动记录进度与断点续传
- 2小时自动停止 (无条数限制)
"""

import time
import json
import os
import signal
import random
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

# ================= 配置参数 =================
TEL_NUMBER = '15180746456'
TEL_NAME = '周建国'

# 进度文件
PROGRESS_FILE = 'progress.json'
LOG_FILE = 'daily_log.txt'

# 页面元素选择器
INPUT_SELECTOR = '.imlp-component-typebox-input'
SEND_BTN_SELECTOR = '.imlp-component-typebox-send-btn'
SLIDER_BTN_SELECTOR = '.passMod_slide-btn'

# 全局变量
TIMEOUT_OCCURRED = False
# ===========================================

def write_log(message):
    """写日志 - 记录运行情况"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)  # GitHub Actions会捕获这个输出
    
    # 同时写入文件
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except Exception:
        pass

def load_progress():
    """加载进度"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    return {"last_index": 0, "completed_cycles": 0}

def save_progress(index, cycles):
    """保存进度"""
    progress = {
        "last_index": index,
        "completed_cycles": cycles,
        "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_log(f"⚠️ 保存进度失败: {e}")

def timeout_handler(signum, frame):
    """2小时超时处理"""
    global TIMEOUT_OCCURRED
    TIMEOUT_OCCURRED = True
    write_log("⏰ 时间到！2小时运行限制已触发")

def get_random_intro():
    """生成随机的病情描述模板"""
    templates = [
        "男，47岁。最近感觉下腹部坠胀，尿频尿急，特别是晚上睡不好，有时候还隐隐作痛，这种情况断断续续好久了，想咨询下怎么治疗。",
        "我是男的，今年47岁。最近老是感觉腰痛，尿频，晚上起夜好几次，严重影响睡眠，想问问这是什么毛病？",
        "男，35岁。最近感觉房事有点力不从心，时间比较短，硬度也不太好，有时候腰酸背痛的，想问问能不能调理。",
        "男，28岁。最近私处有点痒，还有点红肿，小便的时候有刺痛感，不知道是不是感染了什么，有点担心。",
        "你好，我最近身上长了很多红疹子，特别痒，越抓越痒，尤其是晚上，这大概是什么皮肤病啊？",
        "最近皮肤上莫名其妙起了很多小水泡，抓破了还流黄水，用了很多药膏都不管用，想问问专家这是什么原因？",
        "男，47岁。最近老是失眠多梦，头晕耳鸣，血压也有点高，吃西药副作用大，想看看中医。",
        "最近入睡特别困难，躺床上两三个小时都睡不着，白天头昏脑涨的，记忆力也下降了，想问问有没有什么调理的方法。",
        "我最近总是胃胀气，吃完饭就顶着难受，还会反酸烧心，想问问有什么好办法。",
        "男，42岁。最近经常拉肚子，吃稍微油腻一点的东西就肚子痛，去医院检查说是肠胃功能紊乱，想问问中医怎么治。"
    ]
    return random.choice(templates)

def create_browser():
    """创建 DrissionPage 无头浏览器"""
    try:
        co = ChromiumOptions()
        # 无头模式 - 服务器必须开启
        co.set_headless(True)
        # 加载图片 (为了检测滑块)
        co.set_no_imgs(False) 
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # GitHub Actions/Docker 环境必须参数
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        
        return ChromiumPage(addr_driver_opts=co)
        
    except Exception as e:
        write_log(f"❌ 创建浏览器失败: {str(e)}")
        return None

def send_msg(page, text):
    """辅助函数：在输入框发送消息"""
    try:
        # 查找输入框 (2秒超时)
        ele_input = page.ele(INPUT_SELECTOR, timeout=2)
        if not ele_input:
            return False
        
        ele_input.input(text)
        # 拟人化延迟
        time.sleep(random.uniform(0.5, 1.2))
        
        ele_send = page.ele(SEND_BTN_SELECTOR, timeout=2)
        if ele_send:
            ele_send.click()
            write_log(f"📤 发送: {text[:15]}...")
            return True
    except Exception:
        return False
    return False

def process_hospital_page(page, url, index):
    """处理单个页面：包含滑块检测与4轮对话"""
    try:
        write_log(f"🏥 [No.{index + 1}] 正在处理: {url[:50]}...")
        
        # 访问页面
        page.get(url)
        
        # 1. 极速检测滑块 (3秒超时)
        if page.ele(SLIDER_BTN_SELECTOR, timeout=3):
            write_log(f"🚫 [No.{index + 1}] 检测到滑块验证码，跳过。")
            return False

        # 2. 等待输入框加载 (10秒超时)
        if not page.wait.ele_display(INPUT_SELECTOR, timeout=10):
            write_log(f"⚠️ [No.{index + 1}] 输入框未出现，可能加载失败或被拦截。")
            return False

        # === 3. 开始执行 4轮剧本 ===
        
        # [第一轮] 开场白
        if not send_msg(page, "你好，在吗？我想咨询一下病情。"):
            write_log(f"❌ [No.{index + 1}] 第一条消息发送失败。")
            return False
        
        # 模拟等待回复
        time.sleep(random.uniform(3, 5))

        # [第二轮] 病情描述
        intro = get_random_intro()
        send_msg(page, intro)
        time.sleep(random.uniform(4, 6))

        # [第三轮] 留电话
        phone_msg = f"方便电话联系吗？我的电话是{TEL_NUMBER}，{TEL_NAME}。"
        send_msg(page, phone_msg)
        time.sleep(1.5)

        # [第四轮] 致谢
        send_msg(page, "谢谢")
        
        write_log(f"✅ [No.{index + 1}] 剧本执行完毕")
        return True

    except Exception as e:
        write_log(f"❌ [No.{index + 1}] 异常: {str(e)[:100]}")
        return False

def main():
    """主函数"""
    global TIMEOUT_OCCURRED
    TIMEOUT_OCCURRED = False
    
    write_log("=" * 60)
    write_log("🚀 GitHub Actions 智能对话脚本启动 (DrissionPage版)")
    write_log(f"📱 预设号码: {TEL_NUMBER}")
    write_log("=" * 60)
    
    # 设置2小时超时 (仅在Linux/Mac/GitHub Actions有效)
    if hasattr(signal, 'alarm'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(7200) # 7200秒 = 2小时
    
    try:
        # 加载进度
        progress = load_progress()
        start_index = progress['last_index']
        completed_cycles = progress['completed_cycles']
        
        write_log(f"📍 进度恢复: 从第 {start_index + 1} 个开始 (第 {completed_cycles} 轮)")
        
        # 读取网址
        try:
            with open('api.txt', 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            write_log("❌ 错误: 未找到 api.txt 文件")
            return
        
        total_urls = len(urls)
        
        # 创建浏览器
        page = create_browser()
        if not page:
            return
        
        processed_count = 0
        success_count = 0
        
        # 循环处理
        for i in range(start_index, total_urls):
            # 检查退出条件
            if TIMEOUT_OCCURRED:
                break
            
            # 已移除每日50条限制
            
            url = urls[i]
            
            # 执行业务逻辑
            if process_hospital_page(page, url, i):
                success_count += 1
            
            processed_count += 1
            
            # 保存进度
            save_progress(i + 1, completed_cycles)
            
            # 这里的延时是为了防止请求过快导致IP被封，不是为了聊天
            time.sleep(2)
        
        # 检查是否跑完一整轮
        if i >= total_urls - 1:
            completed_cycles += 1
            save_progress(0, completed_cycles)
            write_log(f"🎉 恭喜！已完成第 {completed_cycles} 轮完整循环！")
        
        # 清理资源
        page.quit()
        
        write_log("=" * 60)
        write_log(f"📊 运行总结: 处理 {processed_count} 个, 成功 {success_count} 个")
        write_log("👋 任务结束")
        
    except Exception as e:
        write_log(f"❌ 致命错误: {str(e)}")
    
    finally:
        if hasattr(signal, 'alarm'):
            signal.alarm(0)

if __name__ == '__main__':
    main()
