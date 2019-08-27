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

    def login(self, u='', p='', save=0, path='cookies.json'):
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

        url = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin'
        params = {'s_url': 'https://qzs.qq.com/qzone/v5/loginsucc.html?para=izone'}
        s.get(url, params=params, headers=headers, verify=self.verify)

        url = 'http://check.ptlogin2.qq.com/check'
        params = {'pt_tea': '2', 'uin': self.u, 'appid': '549000912'}
        r = s.get(url, params=params, headers=headers, verify=self.verify)
        ptui_checkVC = r.text[13:-1].replace("'", '').split(',')

        if '0' == ptui_checkVC[0]:
            api = 'https://api.irow.top/qzone/get_sp.php'
            data = {
                'p': self.p,
                'salt': ptui_checkVC[2],
                'vc': ptui_checkVC[1]
            }
            r = requests.post(api, data=data, verify=self.verify)
            sp = r.text

            url = 'https://ssl.ptlogin2.qq.com/login'
            params = {'u': self.u, 'verifycode': ptui_checkVC[1], 'pt_verifysession_v1': ptui_checkVC[3], 'p': sp, 'pt_randsalt': '2',
                      'u1': 'https://qzs.qzone.qq.com/qzone/v5/loginsucc.html?para=izone', 'from_ui': '1', 'pt_uistyle': '40', 'aid': '549000912'}
            r = s.get(url, params=params, headers=headers, verify=self.verify)
            result = r.text[7:-1].replace("'", '').split(',')
            if '登录成功！' == result[4]:
                print('[+]%s' % result[4])
                s.get(result[2], headers=headers, verify=self.verify)
                self.cookies = s.cookies
                self.__get_gtk()
                self.__get_qzonetoken(verify=self.verify)

                if 1 == save:
                    "保存所有cookies"
                    ckdata = {k: v for k, v in s.cookies.items()}
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(ckdata, indent=2))
                        print('[+]保存cookies成功!')
                elif 2 == save:
                    "只保存有意义的cookies"
                    valuesave = ['skey', 'uin', 'p_skey', 'p_uin']
                    ckdata = {k: s.cookies[k] for k in valuesave}
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(ckdata, indent=2))
                        print('[+]保存cookies成功!')
            else:
                print('[-]%s' % result[4])

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
