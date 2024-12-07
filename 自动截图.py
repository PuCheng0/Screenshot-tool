import tkinter as tk
from tkinter import simpledialog, messagebox
import cv2
import numpy as np
from PIL import ImageGrab
import os
import time
from datetime import datetime
from pynput import mouse
import threading

# 输出文件夹
OUTPUT_FOLDER = "./screenshots"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 全局变量
start_point = None
end_point = None
selection_done = False
monitoring = False
monitor_thread = None


def log_message(message):
    """在消息框中添加日志"""
    log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
    log_text.see(tk.END)  # 自动滚动到底部


def select_screen_area():
    """使用鼠标框选屏幕区域"""
    global start_point, end_point, selection_done

    def on_click(x, y, button, pressed):
        global start_point, end_point, selection_done
        if pressed:
            start_point = (x, y)  # 记录起点
        else:
            end_point = (x, y)  # 记录终点
            selection_done = True
            return False  # 停止监听

    messagebox.showinfo("提示", "请使用鼠标框选屏幕区域（按住左键拖动选择区域）")
    log_message("开始选择监控区域")
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

    if start_point and end_point:
        x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
        x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])
        log_message(f"选定区域: ({x1}, {y1}) -> ({x2}, {y2})")
        return x1, y1, x2, y2
    else:
        log_message("未成功选择区域")
        return None


def monitor_screen_area(x1, y1, x2, y2, interval=1, threshold=0.02):
    """监控屏幕区域的变化"""
    global monitoring
    log_message(f"开始监控区域: ({x1}, {y1}, {x2}, {y2})")
    last_image = None  # 存储上一帧画面

    while monitoring:
        # 截取当前画面
        screen = np.array(ImageGrab.grab(bbox=(x1, y1, x2, y2)))
        screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)  # 转换为 BGR 格式

        # 如果有前一帧画面，计算差异
        if last_image is not None:
            diff = cv2.absdiff(screen_bgr, last_image)
            diff_ratio = np.sum(diff) / (255 * diff.size)

            # 如果差异超过阈值，保存截图
            if diff_ratio > threshold:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(OUTPUT_FOLDER, f"{timestamp}.png")
                cv2.imwrite(file_path, screen_bgr)
                log_message(f"画面变化较大（比例: {diff_ratio:.4f}），已保存截图：{file_path}")
#            else:
#                log_message(f"画面变化较小（比例: {diff_ratio:.4f}）")

        # 更新上一帧画面
        last_image = screen_bgr

        # 等待下一次检测
        time.sleep(interval)


def start_monitoring():
    """启动监控"""
    global monitor_thread, monitoring
    if selection_done:
        x1, y1, x2, y2 = selected_area
        interval = float(interval_entry.get() or 1)
        threshold = float(threshold_entry.get() or 0.02)
        monitoring = True
        monitor_thread = threading.Thread(target=monitor_screen_area, args=(x1, y1, x2, y2, interval, threshold))
        monitor_thread.start()
        log_message("监控已启动")
    else:
        log_message("未选择监控区域，请先选择区域")
        messagebox.showerror("错误", "请先选择监控区域！")


def stop_monitoring():
    """停止监控"""
    global monitoring
    monitoring = False
    if monitor_thread:
        monitor_thread.join()
        log_message("监控已停止")
        messagebox.showinfo("提示", "监控已结束")


def select_area():
    """选择屏幕区域"""
    global selected_area, selection_done
    selected_area = select_screen_area()
    if selected_area:
        selection_done = True
    else:
        messagebox.showerror("错误", "未成功选择区域！")


# 创建 GUI 窗口
root = tk.Tk()
root.title("画面监控工具")

# 窗口布局
tk.Label(root, text="监控间隔（秒）:").grid(row=0, column=0, padx=10, pady=10)
interval_entry = tk.Entry(root)
interval_entry.grid(row=0, column=1, padx=10, pady=10)
interval_entry.insert(0, "1")

tk.Label(root, text="变化阈值:").grid(row=1, column=0, padx=10, pady=10)
threshold_entry = tk.Entry(root)
threshold_entry.grid(row=1, column=1, padx=10, pady=10)
threshold_entry.insert(0, "0.02")

select_button = tk.Button(root, text="选择监控区域", command=select_area)
select_button.grid(row=2, column=0, padx=10, pady=10)

start_button = tk.Button(root, text="开始监控", command=start_monitoring)
start_button.grid(row=2, column=1, padx=10, pady=10)

stop_button = tk.Button(root, text="结束监控", command=stop_monitoring)
stop_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

# 添加消息框
log_text = tk.Text(root, height=4, width=50, state=tk.NORMAL)
log_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# 启动 GUI 主循环
try:
    root.mainloop()
except KeyboardInterrupt:
    log_message("程序被中断")
