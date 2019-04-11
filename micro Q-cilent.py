#!/usr/bin/python3
# _*_coding:utf-8_*_
'''
这是Micro Q的客户端
技术点:
    1.tkinter界面
    2.类封装
    3.线程
    4.wx模块图形用户界面
    5.消息以json文件格式发送
'''
# 导入相关模块
from socket import *
from threading import Thread
import wx
import os
from tkinter import filedialog
import tkinter
import json
import wx.lib.agw.customtreectrl as CT

root = tkinter.Tk()
root.withdraw()  # ****实现主窗口隐藏


# 定义类,继承自父类wx.Frame
class QICQ(wx.Frame):
    # 初始化定义一些函数
    def __init__(self):
        global serverIp, serverPort
        serverPort = 6789
        serverIp = '127.0.0.1'

        # 初始化定义窗口属性(背景色,按钮,大小,位置)和线程

        # 设置主窗口,这里定义的是一个超类
        wx.Frame.__init__(self, parent=None, title='micro_Q', size=(600, 400))
        # 创建智能拉伸窗口
        panel = wx.Panel(self)
        panel.SetBackgroundColour((0, 153, 255))

        # 进行是否有选择的断言
        # 断言是否有选择文件框
        self.isChoosedFile = False
        self.dataOfChoosedFile = None
        self.fileName = None

        # 用户部分
        # 属性结构的全选或取消
        self.UserListTree = CT.CustomTreeCtrl(parent=panel, pos=(10, 10), size=(280, 300),
                                              style=wx.TR_FULL_ROW_HIGHLIGHT)
        # 创建根目录,添加的为根的名称
        self.rootID = self.UserListTree.AddRoot("已登录用户")
        # 设置背景色
        self.UserListTree.SetBackgroundColour((224, 255, 255))
        # 添加子节点
        self.UserListTree.AppendItem(self.rootID, '第一个子节点')
        self.UserListTree.AppendItem(self.rootID, '第二个子节点')
        # 展开所有节点
        self.UserListTree.ExpandAll()
        self.UserList = []
        # 构建说明按钮
        self.info = wx.Button(parent=panel, pos=(100, 315), size=(80, 40), label="说明")
        # 设置背景色
        self.info.SetBackgroundColour((224, 255, 255))

        # 操作部分
        # 文本输入框
        # 创建文本控件对象,设置前景颜色即文本颜色
        inputTip = wx.TextCtrl(parent=panel, pos=(300, 10), size=(130, 20), value="请输入你要发送的信息", style=wx.TE_READONLY)
        # 设置背景颜色
        inputTip.SetBackgroundColour((224, 255, 255))
        # 设置分割线
        self.input = wx.TextCtrl(parent=panel, pos=(300, 30), size=(130, 50))
        self.input.SetForegroundColour((0, 153, 255))
        self.input.SetBackgroundColour((224, 255, 255))

        # 文件选择框
        self.fileChooser = wx.Button(parent=panel, pos=(440, 10), size=(130, 70), label="选择文件")
        self.fileChooser.SetBackgroundColour((224, 255, 255))

        # 发送按钮
        self.send = wx.Button(parent=panel, pos=(300, 100), size=(275, 50), label="发送")
        self.send.SetBackgroundColour((224, 255, 255))
        # 中间分割线
        separation = wx.TextCtrl(parent=panel, pos=(290, 170), size=(300, 2))
        separation.SetBackgroundColour((224, 255, 255))
        # 接收消息框
        receivedTip = wx.TextCtrl(parent=panel, pos=(300, 190), size=(135, 20), value="发送/接收到的消息列表",
                                  style=wx.TE_READONLY)
        receivedTip.SetForegroundColour((0, 153, 255))
        receivedTip.SetBackgroundColour((224, 255, 255))
        # 设置文本框的滚动方式style
        self.messageList = wx.TextCtrl(parent=panel, size=(275, 120), pos=(300, 210),
                                       style=(wx.TE_MULTILINE | wx.HSCROLL | wx.TE_READONLY))
        self.messageList.SetBackgroundColour((224, 255, 255))
        self.messageList.SetForegroundColour((0, 153, 255))

        # 处理要发送的信息,进行初始值定义
        self.sendMessage = ''

        # 创建线程
        childThraed = Thread(target=self.socketHander)
        childThraed.setDaemon(True)
        childThraed.start()

        # 绑定按钮事件
        self.Bind(wx.EVT_BUTTON, self.OnInfoClicked, self.info)
        self.Bind(wx.EVT_BUTTON, self.OnSendClicked, self.send)
        self.Bind(wx.EVT_BUTTON, self.OnFileChooseClicked, self.fileChooser)

    # 说明按钮事件函数
    def OnInfoClicked(self, event):
        wx.MessageDialog(self, u'''\r\n\r\n\r\n\t\t1、互联的环境必须是在同一个局域网\r\n
                2、必须先在左边选择发送对象且发送消息不为空才能发送消息\r\n
                3、选择根目录{已登录用户}是群发消息，选择单个是私发消息\r\n
                4、刚登录时最后一个ip是你自己的ip\r\n''', u"警告", wx.OK).ShowModal()

    # 处理发送按钮
    def OnSendClicked(self, event):
        # 获取输入框输入的值
        self.sendMessage = self.input.Value
        # 如果输入的值不存在且未选择文件,报出警告信息
        if len(self.sendMessage) == 0 and self.fileChooser == False:
            wx.MessageDialog(self, u"请先输入(选择)待发送的消息(文件)", u"警告", wx.OK).ShowModal()
            return None
        # 选择发送用户
        selected = self.UserListTree.GetSelection()
        selected = self.UserListTree.GetItemText(selected)
        # 如果未选择发送用户,报出警告信息
        if not selected:
            wx.MessageDialog(self, u"请先选择用户或组", u"警告", wx.OK).ShowModal()
            return None

        # 如果选择的是根节点,转发群消息
        if selected == "已登录用户":
            # 如果未选择文件
            if self.isChoosedFile == False:
                self.sendMessage = {
                    "type": "2",
                    "sourceIP": self.ip,
                    "destinationIP": selected,
                    "content": self.sendMessage
                }
            # 选择了文件
            else:
                self.sendMessage = {
                    "type": "5",
                    "sourceIP": self.ip,
                    "destinationIP": selected,
                    "filename": self.fileName,
                    "content": self.dataOfChoosedFile
                }
        # 如果不是,转发给单人
        else:
            if self.isChoosedFile == False:
                self.sendMessage = {
                    "type": "1",
                    "sourceIP": self.ip,
                    "destinationIP": selected,
                    "content": self.sendMessage
                }
            else:
                self.sendMessage = {
                    "type": "4",
                    "sourceIP": self.ip,
                    "destinationIP": selected,
                    "filename": self.fileName,
                    "content": self.dataOfChoosedFile
                }

    # 处理文件选择按钮
    def OnFileChooseClicked(self, event):
        filepath = filedialog.askopenfilename(title="请选择要发送的文件")
        if len(filepath) > 0:
            filedicpath, fullflname = os.path.split(filepath)
            self.fileName = fullflname
            self.isChoosedFile = True
            with open(filepath, "r") as f:
                self.dataOfChoosedFile = f.read()

        print(self.fileName)

    # 消息收发处理
    def socketHander(self):
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.connect((serverIp, serverPort))
        self.clientSocket.settimeout(2)
        self.ip, self.port = self.clientSocket.getsockname()
        print("self ip", self.ip)
        while True:
            # 发送消息
            if len(self.sendMessage) == 0:
                pass
            else:
                if self.isChoosedFile == True:
                    self.clientSocket.send(json.dumps(self.sendMessage).encode("utf-8"))
                    self.messageList.AppendText("文件[" + self.fileName + "]发送成功\r\n")
                    self.fileName = None
                    self.dataOfChoosedFile = None
                    self.isChoosedFile = False
                    self.sendMessage = ""

                else:
                    self.clientSocket.send(json.dumps(self.sendMessage).encode("utf-8"))
                    self.messageList.AppendText("消息[" + self.sendMessage.get("content") + "]发送成功\r\n")
                    self.input.SetLabelText("")
                    self.sendMessage = ""

            try:
                # 接收消息
                receivedMessage = self.clientSocket.recv(1024)
                receivedMessage = receivedMessage.decode("utf-8")
                receivedMessage = json.loads(receivedMessage)
                print(receivedMessage)
                type = receivedMessage.get("type")

                # 客户端接收服务端发来的转发消息
                if type == "1":
                    print("客户端收到消息")
                    sourceIp = receivedMessage.get("sourceIP")
                    content = receivedMessage.get("content")
                    if sourceIp == self.ip:
                        pass
                    else:
                        self.messageList.AppendText("来自:[" + sourceIp + "]的消息:[" + content + "]\r\n")

                elif type == "2":
                    # 客户端接收服务端发来的刷新列表请求
                    self.userList = receivedMessage.get("content")
                    self.setUserList()

                elif type == "3":
                    filename = receivedMessage.get("filename")
                    print("rrrr", filename)
                    with open(filename, "w") as f:
                        f.write(receivedMessage.get("content"))
            except:
                print("等待数据...")
                pass
        pass

    # 设置添加用户
    def setUserList(self):
        self.UserListTree.DeleteChildren(self.rootID)
        for user in self.userList:
            # if user == self.ip:
            #     continue
            self.UserListTree.AppendItem(self.rootID, user)
        pass

    # 关闭
    def OnClose(self, event):
        endMessage = {
            "type": "3",
            "content": "bye"
        }
        self.clientSocket.send(json.dumps(endMessage).encode("utf-8"))
        self.Destroy()


if __name__ == '__main__':
    global serverIp
    serverIp = input("请输入服务器ip")
    app = wx.App()
    frame = QICQ()
    # frame.Bind(wx.EVT_CLOSE, frame.OnClosed)
    frame.Show()
    app.MainLoop()
    app.OnExit()
