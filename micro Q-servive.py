#!/usr/bin/python3
# _*_coding:utf-8_*_
'''
micro Q-survive
功能:
    1.群聊,单聊,传输文件
    2.处理消息内容
    3.server端
'''
# 导入响应模块
from socket import *
from threading import Thread
import time
import json

# 定义连接端口连接ip的全局变量
serverPort = 6789
serverIp = '127.0.0.1'
connectionSocketList = []


# 更新连接的地址
def updateConnectionList():
    global connectionSocketList
    connectionSocketIPList = []
    for item in connectionSocketList:
        ip, port = item.getpeername()
        connectionSocketIPList.append(ip)
        print(ip)
    return {
        "type": "2",
        "content": connectionSocketIPList
    }


# 处理接收消息
def socket_message(connectionSocket):
    global connectionSocketList
    connectionSocketList.append(connectionSocket)
    connectionSocket.settimeout(2)
    for socket in connectionSocketList:
        socket.send(json.dumps(updateConnectionList()).encode("utf-8"))
    # 循环接收消息
    while True:
        # 发送过来的消息是经过二进制编码的
        recvMessage = connectionSocket.recv(1024)
        if not recvMessage:
            time.sleep(1)
            continue
        # 将消息进解码操作
        recvMessage = recvMessage.decode('utf-8')
        # 将解码后的消息(字符串)进行json格式初始化(json.loads())
        recvMessage = json.loads(recvMessage)
        # 按json对象取值,这里要保证客户端发来的json格式也是json类型
        type = recvMessage.get("type")
        # 按类型判断信息内容
        # 服务器转发单人聊天消息
        if type == "1":
            dip = recvMessage.get("destinationIP")
            for socket in connectionSocket:
                sip, sport = socket.getpeername()
                print("sip", sip)
                if sip == dip:
                    message = {
                        "type": "1",
                        "sourceIP": recvMessage.get("sourceIP"),
                        "content": recvMessage.get("content")
                    }
                    socket.send(json.dumps(message).encode("utf-8"))

        # 服务器转发群消息
        elif type == "2":
            # 遍历groupList
            message = {
                "type": "1",
                "sourceIP": recvMessage.get("sourceIP"),
                "content": recvMessage.get("content")
            }
            for socket in connectionSocket:
                socket.send(json.dumps(message).encode("utf-8"))



        # 客户端想要断开连接
        elif type == "3":
            connectionSocket.remove(connectionSocket)
            # 通知所有人xxx已下线
            for socket in connectionSocket:
                socket.send(json.dumps(updateConnectionList()).encode("utf-8"))

        elif type == "4":
            dip = recvMessage.get("destinationIP")
            for socket in connectionSocket:
                sip, sport = socket.getpeername()
                print("sip", sip)
                if sip == dip:
                    message = {
                        "type": "3",
                        "sourceIP": recvMessage.get("sourceIP"),
                        "filename": recvMessage.get("filename"),
                        "content": recvMessage.get("content")
                    }
                    socket.send(json.dumps(message).encode("utf-8"))

        elif type == "5":
            message = {
                "type": "3",
                "sourceIP": recvMessage.get("sourceIP"),
                "filename": recvMessage.get("filename"),
                "content": recvMessage.get("content")
            }
            for socket in connectionSocket:
                socket.send(json.dumps(message).encode("utf-8"))


# 处理套接字网络设置,线程创建,主程序运行
if __name__ == "__main__":
    # 基于流失套接字通信
    serverSocket = socket(AF_INET, SOCK_STREAM)
    # 绑定连接地址
    serverSocket.bind((serverIp, serverPort))
    # 设置最大监听数
    serverSocket.listen(20)
    while True:
        # 循环接收
        connectionSocket, addr = serverSocket.accept()
        #  getpeername函数检索到一个插座相连的对端的地址。
        print('连接的地址为:', connectionSocket.getpeername())
        # 启动线程target 绑定线程函数,args 元组给绑定参数传参
        Thread(target=socket_message, args=(connectionSocket,)).start()
