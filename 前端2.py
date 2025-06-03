import tkinter as tk
from PIL import Image, ImageTk
import os
import play
import Modelarts
import main
from huaweicloud_sis.exception.exceptions import ClientException
from huaweicloud_sis.exception.exceptions import ServerException

class SimpleChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 聊天室")
        self.root.geometry("600x600")
        self.root.minsize(800, 480)
        self.root.configure(bg="#9F1254")
        
        # 配置字体
        self.base_font = ("Microsoft YaHei", 12)
        self.button_font = ("Microsoft YaHei", 10, "bold")
        
        # 加载喇叭图标
        self.speaker_icon = self._load_speaker_icon(
            r"C:\Users\19122\Desktop\软件工程\实验\代码\播放.webp"
        )

        # 主容器布局
        main_frame = tk.Frame(root, bg="#FFFFFF")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 聊天区域容器（可滚动部分）
        chat_container = tk.Frame(main_frame, bg="#FFFFFF")
        chat_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 创建Canvas和滚动条
        self.chat_canvas = tk.Canvas(chat_container, bg="#FFFFFF", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(chat_container, orient=tk.VERTICAL)
        
        # 配置滚动关联
        self.scrollbar.config(command=self.chat_canvas.yview)
        self.chat_canvas.config(yscrollcommand=self.scrollbar.set)
        
        # 布局聊天组件
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 背景图片处理
        self.bg_image_item = None
        self.original_bg_image = None
        try:
            self.background_image = Image.open(r"C:\Users\19122\Desktop\软件工程\实验\代码\背景.png")
            self.original_bg_image = self.background_image.copy()
            self.bg_image_item = self.chat_canvas.create_image(0, 0, image=None, anchor=tk.NW, tags="bg")
        except Exception as e:
            print(f"背景图片加载失败: {str(e)}")

        # 消息系统初始化
        self.message_history = []
        self.last_y = 0

        # 底部固定输入区
        bottom_frame = tk.Frame(main_frame, bg="#FFFFFF")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 5))

        # 输入组件容器
        input_container = tk.Frame(bottom_frame, bg="#FFFFFF")
        input_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 输入框
        self.input_box = tk.Entry(
            input_container,
            font=self.base_font,
            bg="white",
            relief=tk.GROOVE,
            borderwidth=2
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_box.bind("<Return>", self.send_message)

        # 发送按钮
        self.send_btn = tk.Button(
            input_container,
            text="发送",
            command=self.send_message,
            font=self.button_font,
            bg="#1A73E8",
            fg="white",
            activebackground="#1557B0",
            relief=tk.FLAT
        )
        self.send_btn.pack(side=tk.LEFT)

        # 喇叭按钮
        self.sound_btn = tk.Button(
            bottom_frame,
            command=self.play_sound,
            image=self.speaker_icon,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            activebackground="#EEEEEE",
            bg="#FFFFFF"
        )
        self.sound_btn.image = self.speaker_icon
        self.sound_btn.pack(side=tk.RIGHT, padx=5)
        
        # 悬停效果
        self.sound_btn.bind("<Enter>", self._on_btn_hover)
        self.sound_btn.bind("<Leave>", self._on_btn_leave)

        # Canvas事件绑定
        self.chat_canvas.bind("<Configure>", self._on_canvas_configure)

        # 初始化欢迎消息
        self._update_chat("System", "欢迎来到聊天室！", "system")

    def _load_speaker_icon(self, path):
        """加载喇叭图标"""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"文件不存在: {path}")
            original_image = Image.open(path)
            resized_image = original_image.resize((30, 30), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(resized_image)
        except Exception as e:
            print(f"图标加载失败: {str(e)}")
            return ImageTk.PhotoImage(Image.new("RGBA", (30,30), (255,255,255,0)))

    def _on_btn_hover(self, event):
        """按钮悬停效果"""
        event.widget.config(bg="#F5F5F5")

    def _on_btn_leave(self, event):
        """按钮离开效果"""
        event.widget.config(bg="#FFFFFF")

    def send_message(self, event=None):
        """处理消息发送"""
        message = self.input_box.get().strip()
        if not message:
            return

        self._update_chat("You", message, "user")
        self.input_box.delete(0, tk.END)
        
        # 模拟AI回复
        ai_response = Modelarts.play(message)
        self._update_chat("AI", ai_response, "ai")
        try:
            main.ttsc_example(ai_response)
        except ClientException as e:
            print(e)
        except ServerException as e:
            print(e)

    def play_sound(self):
        """播放音效"""
        play.play()

    def _on_canvas_configure(self, event):
        """画布尺寸变化处理"""
        self._resize_background(event)
        self._update_message_width(event)
        self._update_scrollregion()

    def _resize_background(self, event):
        """调整背景图片尺寸"""
        if self.original_bg_image:
            resized_image = self.original_bg_image.resize(
                (event.width, event.height),
                Image.Resampling.LANCZOS
            )
            self.bg_photo = ImageTk.PhotoImage(resized_image)
            self.chat_canvas.itemconfig(self.bg_image_item, image=self.bg_photo)

    def _update_message_width(self, event):
        """更新消息换行宽度"""
        self.chat_canvas.itemconfigure("message", width=event.width - 20)
        self._redraw_messages()

    def _redraw_messages(self):
        """重绘所有消息"""
        self.chat_canvas.delete("message")
        self.last_y = 0
        for msg in self.message_history:
            self._create_message_item(msg)

    def _create_message_item(self, msg):
        """创建消息项"""
        text_id = self.chat_canvas.create_text(
            10, self.last_y,
            text=f"{msg['sender']}: {msg['content']}",
            anchor=tk.NW,
            fill=msg['color'],
            font=self.base_font,
            width=self.chat_canvas.winfo_width() - 20,
            tags=("message",)
        )
        bbox = self.chat_canvas.bbox(text_id)
        if bbox:
            self.last_y = bbox[3] + 5

    def _update_scrollregion(self):
        """更新滚动区域"""
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)

    def _update_chat(self, sender, message, tag="system"):
        """更新聊天内容"""
        color_map = {
            "system": "#666666",
            "user": "#1A73E8",
            "ai": "#031009"
        }
        
        new_msg = {
            'sender': sender,
            'content': message,
            'color': color_map[tag]
        }
        self.message_history.append(new_msg)
        self._create_message_item(new_msg)
        self._update_scrollregion()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleChatApp(root)
    root.mainloop()