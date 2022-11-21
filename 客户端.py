
from socket import *
import sys
import base64
from PyQt5.QtWidgets import *
from PyQt5 import uic
    
class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.ui=uic.loadUi("./first.ui")
        #UI界面的输入值
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.Server=self.ui.Input_Server#得到服务器网站
        self.UserName=self.ui.Input_UserName#得到发送者用户名
        self.SenderMail=self.ui.Input_SenderMail#得到发送者邮箱
        self.ACode=self.ui.Input_ACode#得到发送者授权码
        self.ReceiveEmail=self.ui.Input_ReceiveEmail #得到接收者邮箱
        self.Title=self.ui.Input_Title#得到新建标题
        self.Content=self.ui.Input_Content #得到写信内容
        self.Output=self.ui.Output_status #得到状态输出栏
        #UI界面的按钮
        btn_save=self.ui.Button_save#保存发件人信息，并与服务器连接
        btn_break=self.ui.Button_break#中断与服务器的连接
        btn_send=self.ui.Button_Send#发送信件
        #print(*self.ui.__dict__,sep="\n")

        #开始给按钮绑定槽函数
        btn_save.clicked.connect(self.Login_and_connect)
        btn_send.clicked.connect(self.Send)
        btn_break.clicked.connect(self.quit)
   
    def Login_and_connect(self):#登录并且与服务器连接

        # 1.创建客户端套接字并建立TCP连接
        serverPort = 25  # SMTP使用25号端口
        mailServer=str(self.Server.text())
        
        self.clientSocket.connect((mailServer, serverPort))  # connect只能接收一个参数
        # 2.从客户套接字中接收信息
        recv = self.clientSocket.recv(1024).decode()
        self.Output.append(recv)
        self.Output.repaint()
        if '220' != recv[:3]:
            self.Output.append('220 reply not received from server.')
            self.Output.append('未收到服务器回复，连接失败')
            return
        self.Output.append("成功与服务器连接")
        # 3.发送 HELO 命令并且打印服务端回复
        # 开始与服务器的交互，服务器将返回状态码250,说明请求动作正确完成
        heloCommand = 'HELO Alice\r\n'
        self.clientSocket.send(heloCommand.encode())  # 随时注意对信息编码和解码
        recv1 = self.clientSocket.recv(1024).decode()
        self.Output.append(recv1)
        if '250' != recv1[:3]:
            self.Output.append('250 reply not received from server.')
            self.Output.append('未收到服务器回复，连接失败')
            return
        # 4.发送"AUTH LOGIN"命令，验证身份.服务器将返回状态码334（服务器等待用户输入验证信息）
        self.clientSocket.sendall('AUTH LOGIN\r\n'.encode())
        recv2 = self.clientSocket.recv(1024).decode()
        self.Output.append(recv2)
        if '334' != recv2[:3]:
            self.Output.append('334 reply not received from server.')
            self.Output.append('未收到服务器回复，验证身份请求失败')
            return
        # 5.发送验证信息
        username=str(self.UserName.text())
        username=base64.b64encode(username.encode('utf-8')).decode("utf-8")
        password=str(self.ACode.text())
        password=base64.b64encode(password.encode('utf-8')).decode("utf-8")
        self.clientSocket.sendall((username + '\r\n').encode())
        recvName = self.clientSocket.recv(1024).decode()
        self.Output.append(recvName)
        if '334' != recvName[:3]:
            self.Output.append('334 reply not received from server')
            self.Output.append('未收到服务器回复，账号验证失败')
            return
        self.clientSocket.sendall((password + '\r\n').encode())
        recvPass = self.clientSocket.recv(1024).decode()
        self.Output.append(recvPass)
        self.Output.append('账号验证成功')
            # 如果用户验证成功，服务器将返回状态码235
        if '235' != recvPass[:3]:
            self.Output.append('235 reply not received from server')
            self.Output.append('未收到服务器回复，授权码验证失败')
            return
        self.Output.append('授权码验证成功')
        
    def Send(self):
        # TCP连接建立好之后，通过用户验证就可以开始发送邮件。
        # 邮件的传送从MAIL命令开始，MAIL命令后面附上发件人的地址。
        # 1.发送 MAIL FROM 命令，并包含发件人邮箱地址
        fromAddress=str(self.SenderMail.text())
        self.clientSocket.sendall(('MAIL FROM: <' + fromAddress + '>\r\n').encode())
        recvFrom = self.clientSocket.recv(1024).decode()
        self.Output.append(recvFrom)
        if '250' != recvFrom[:3]:
            self.Output.append('250 reply not received from server')
            self.Output.append('未收到服务器回复')
            return
        # 2.接着SMTP客户端发送一个或多个RCPT (收件人recipient的缩写)命令，格式为RCPT TO: <收件人地址>。
        # 发送 RCPT TO 命令，并包含收件人邮箱地址，返回状态码 250
        toAddress=str(self.ReceiveEmail.text())
        self.clientSocket.sendall(('RCPT TO: <' + toAddress + '>\r\n').encode())
        recvTo = self.clientSocket.recv(1024).decode()  # 注意UDP使用sendto，recvfrom
        self.Output.append(recvTo)
        if '250' != recvTo[:3]:
            self.Output.append('250 reply not received from server')
            self.Output.append('未收到服务器回复')
            return
        # 3.发送 DATA 命令，表示即将发送邮件内容。服务器将返回状态码354（开始邮件输入，以"."结束）
        self.clientSocket.send('DATA\r\n'.encode())
        recvData = self.clientSocket.recv(1024).decode()
        self.Output.append(recvData)
        if '354' != recvData[:3]:
            self.Output.append('354 reply not received from server')
            self.Output.append('未收到服务器回复')
            return
        # 4.编辑邮件信息，发送数据
        subject = str(self.Title.text())
        contentType = "text/plain"
        msg=str(self.Content.toPlainText())
        message = 'from:' + fromAddress + '\r\n'
        message += 'to:' + toAddress + '\r\n'
        message += 'subject:' + subject + '\r\n'
        message += 'Content-Type:' + contentType + '\t\n'
        message += '\r\n' + msg
        self.clientSocket.sendall(message.encode())
        # 5.以"."结束。请求成功返回 250
        endMsg = "\r\n.\r\n"
        self.clientSocket.sendall(endMsg.encode())
        recvEnd = self.clientSocket.recv(1024).decode()
        self.Output.append(recvEnd)
        if '250' != recvEnd[:3]:
            self.Output.append('250 reply not received from server')
            self.Output.append('未收到服务器回复')
            return

    def quit(self):
        self.clientSocket.sendall('QUIT\r\n'.encode())
        self.clientSocket.close()
if __name__=='__main__':
    app=QApplication(sys.argv)
    w=MyWindow()
    w.ui.show()
    app.exec()
    