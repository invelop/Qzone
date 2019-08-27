# coding=utf-8
import requests
import re
import json


class Qzone(object):
    """Class that implements common functions of Qzone.

    Log in and get cookies.

    Attributes:
        u: Your QQ number.
        p: Your password.
        cookies: Cookies that maintain login status.
    """

    def __init__(self, u='', p='', cookies={}, verify=True, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}):
        """Initialize class by user information."""
        self.u = u
        self.p = p
        self.verify = verify
        self.__headers = headers
        self.cookies = cookies
        self.g_tk = ''
        self.qzonetoken = ''

    def login(self, u='', p=''):
        """Log in and get cookies"""
        if '' == self.u or '' == self.p:
            if '' == u or '' == p:
                raise ValueError('QQ number and password are required!')
            else:
                self.u = u
                self.p = p
        if not self.u.isdigit():
            raise ValueError('QQ number must be numbers!')

        headers = self.__headers
        s = requests.Session()

        # 获取初始cookies
        url = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin'
        params = {'s_url': 'https://qzs.qq.com/qzone/v5/loginsucc.html?para=izone'}
        s.get(url, params=params, headers=headers, verify=self.verify)

        # 获取登录参数
        url = 'http://check.ptlogin2.qq.com/check'
        params = {'pt_tea': '2', 'uin': self.u, 'appid': '549000912'}
        r = s.get(url, params=params, headers=headers, verify=self.verify)
        ptui_checkVC = r.text[13:-1].replace("'", '').split(',')

        # 检验验证码
        if '0' == ptui_checkVC[0]:
            # 获取加密后的密码
            api = 'https://api.irow.top/qzone/get_sp.php'
            data = {
                'p': self.p,
                'salt': ptui_checkVC[2],
                'vc': ptui_checkVC[1]
            }
            r = requests.post(api, data=data, verify=self.verify)
            sp = r.text

            # 登录
            url = 'https://ssl.ptlogin2.qq.com/login'
            params = {'u': self.u, 'verifycode': ptui_checkVC[1], 'pt_verifysession_v1': ptui_checkVC[3], 'p': sp, 'pt_randsalt': '2',
                      'u1': 'https://qzs.qzone.qq.com/qzone/v5/loginsucc.html?para=izone', 'from_ui': '1', 'pt_uistyle': '40', 'aid': '549000912'}
            r = s.get(url, params=params, headers=headers, verify=self.verify)
            ptuiCB = r.text.strip("ptuiCB( )").replace("'", '').split(',')

            # 检验登录情况
            if '登录成功！' == ptuiCB[4]:
                print('[+]%s' % ptuiCB[4])
                s.get(ptuiCB[2], headers=headers, verify=self.verify)
                self.cookies = s.cookies
                self.__get_gtk()
                self.__get_qzonetoken()
            else:
                print('[-]%s' % ptuiCB[4])
        else:
            print('[-]登录失败！需要输入验证码！')
            print('[+]已自动为您切换为扫码登录！')
            qrlogin()

    def qrlogin(self, s=3):
        headers = self.__headers
        s = requests.Session()

        # 获取初始cookies
        url = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin'
        params = {'s_url': 'https://qzs.qq.com/qzone/v5/loginsucc.html?para=izone'}
        s.get(url, params=params, headers=headers, verify=self.verify)

        # 获取二维码
        url = 'https://ssl.ptlogin2.qq.com/ptqrshow'
        params = {
            "appid": "549000912",
            #"e": "2",
            #"l": "M",
            "s": s,  # 二维码尺寸
            #"d": "72",
            #"v": "4",
            #"t": "0.06670120586595374",
            #"daid": "5",
            #"pt_3rd_aid": "0"
        }
        r = s.get(url, params=params, headers=headers, verify=self.verify)
        with open('qrcode.png', 'wb') as f:
            f.write(r.content)
        ptqrtoken = get_qrtoken(s.cookies['qrsig'])

        # 检验登录状态
        while True:
            url = 'https://ssl.ptlogin2.qq.com/ptqrlogin'
            params = {
                "u1": "https://qzs.qzone.qq.com/qzone/v5/loginsucc.html?para=izone",
                "ptqrtoken": ptqrtoken,
                #"ptredirect": "0",
                #"h": "1",
                #"t": "1",
                #"g": "1",
                "from_ui": "1",
                #"ptlang": "2052",
                #"action": "0-0-%d" % (date_to_millis(datetime.datetime.utcnow()) - start_time),
                #"js_ver": "19081313",
                #"js_type": "1",
                #"login_sig": s.cookies['pt_login_sig'],
                #"pt_uistyle": "40",
                "aid": "549000912",
                #"daid": "5",
                # "ptdrvs": s.cookies['ptdrvs'],
                #"has_onekey": "1"
            }
            r = s.get(url, params=params, headers=headers, verify=self.verify)
            ptuiCB = r.text.strip("ptuiCB( )").replace("'", '').split(',')
            # 65: QRCode 失效, 0: 验证成功, 66: 未失效, 67: 验证中
            if '0' == ptuiCB[0]:
                print('[+]%s' % ptuiCB[4])
                s.get(ptuiCB[2], headers=headers, verify=self.verify)
                self.cookies = s.cookies
                self.__get_gtk()
                self.__get_qzonetoken()
                break
            elif '65'==ptuiCB[0]:
                print('[-]%s' %ptuiCB[4])
                print('[+]检测到二维码已失效，已为您重新获取')

                # 获取二维码
                url = 'https://ssl.ptlogin2.qq.com/ptqrshow'
                params = {
                    "appid": "549000912",
                    #"e": "2",
                    #"l": "M",
                    "s": s,  # 二维码尺寸
                    #"d": "72",
                    #"v": "4",
                    #"t": "0.06670120586595374",
                    #"daid": "5",
                    #"pt_3rd_aid": "0"
                }
                r = s.get(url, params=params, headers=headers, verify=self.verify)
                with open('qrcode.png', 'wb') as f:
                    f.write(r.content)
                ptqrtoken = get_qrtoken(s.cookies['qrsig'])
            else:
                print('[-]%s' % ptuiCB[4])
            time.sleep(5)


    def __get_gtk(self):
        skey = self.cookies['skey']
        hash = 5381
        for i in skey:
            hash = hash + (hash << 5) + ord(i)
        self.g_tk = hash & 0x7fffffff

    def __get_qzonetoken(self):
        headers = self.__headers
        url = 'https://user.qzone.qq.com/%s' % self.u
        r = requests.get(url, headers=headers,
                         cookies=self.cookies, verify=self.verify)
        pattern = 'window.g_qzonetoken = \(function\(\)\{ try\{return "(.+?)";\}'
        result = re.search(pattern, r.text)
        qzonetoken = result.group(1)
        self.qzonetoken = qzonetoken

    def __get_qrtoken(qrsig):
        e = 0
        for i in qrsig:
            e += (e << 5) + ord(i)
        return 2147483647 & e

    def get_info(self, model=1):
        if 1 == model:
            result = {'u': self.u, 'p': self.p, 'cookies': {
                k: v for k, v in self.cookies.items()}, 'g_tk': self.g_tk, 'qzonetoken': self.qzonetoken}
        elif 2 == model:
            valuesave = ['skey', 'uin', 'p_skey', 'p_uin']
            result = {'u': self.u, 'p': self.p, 'cookies': {
                k: self.cookies[k] for k in valuesave}, 'g_tk': self.g_tk, 'qzonetoken': self.qzonetoken}
        return result

    def right_frame(self):
        headers = self.__headers
        url = 'https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/right_frame.cgi'
        params = {
            "uin": self.u,
            "param": f"3_{self.u}_0|14_{self.u}|8_8_{self.u}_0_1_0_0_1|10|11|12|13_3|17|20|9_0_8_1|18",
            "g_tk": self.g_tk,
            "qzonetoken": self.qzonetoken
        }
        r = requests.get(url, params=params, headers=headers,
                         cookies=self.cookies, verify=self.verify)
        result = json.loads(r.text.strip(
            '_Callback() \n\t\r').replace("'", '"'))
