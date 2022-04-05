"""line_bot_router.py: lineボット用ルーター
複数のコマンドと複数のサブコマンドがある場合に便利
例えば:

「天気」：　東京の天気を表示
「天気　<地名>」：<地名>の天気を表示
のようなコマンドを作るとき、

```python
root_router = Router()


@root_router.register('天気')
def weather(event):
    '''天気: 東京の天気を表示'''
    text = get_weather(name='Tokyo')
    return TextSendMessage(text=text)


@weather.register('.+')  # 正規表現でパターンを登録  「天気 xxxx」にマッチする
def weather_tomorrow(event):
    '''天気 <地名>: <地名>の天気を表示'''
    msg = event.message.text
    text = get_weather(name=msg)
    return TextSendMessage(text=text)


help_msg = root_router.make_description_text()
print(help_msg)
# =>
# 天気: 東京の天気を表示
# 天気 <地名>: <地名>の天気を表示

```


とすると、
「天気」
と
「天気 <地名>」
の両方が登録される。
LineBOTのハンドラにroot_router.processを割り当てると自動的にサブコマンドまで検索してくれる
"""

from functools import wraps
import re

from linebot.models import TextSendMessage


class Router:

    __doc__ = ""

    @property
    def __doc__(self):
        return self.func.__doc__

    @__doc__.getter
    def __doc__(self):
        return self.func.__doc__

    def __init__(self, default=None):
        self.pattern = re.compile("")
        self.child_routers = []
        self.func = lambda evt: None
        self.reply_only = []
        self.default = default
        self.name = ""
        self.parent = None

    def user_limited(self):
        return bool(self.reply_only)

    def make_description_text(self) -> str:
        """自分の子Router以下のdocstringを全て抜き出し
        改行で連結した文字列を返す"""
        lines = []
        if self.__doc__:
            lines.append(self.__doc__)

        def _recur(router):
            if not router.child_routers:
                return
            for r in router.child_routers:
                if r.__doc__:
                    lines.append(r.__doc__)
                _recur(r)

        _recur(self)
        return "\n".join(lines)

    def message(self, evt):
        return self.func(evt)

    def process(self, evt):
        msg = evt.message.text
        send_msg = None
        head, *tails = msg.split()
        user_id = evt.source.user_id

        for router in self.child_routers:
            if router.pattern.match(head):
                if router.user_limited():
                    if user_id not in router.reply_only:
                        send_msg = router.default
                        if send_msg is None:
                            continue
                        else:
                            break
                if tails:
                    evt.message.text = " ".join(tails)
                    send_msg = router.process(evt)
                else:
                    send_msg = router.message(evt)
                if send_msg:
                    break
        if send_msg is None and self.default:
            send_msg = self.default
        return send_msg

    def register(self, pattern, default=None):
        def _register(func):
            h = Router(default=default)
            h.pattern = re.compile(pattern)
            h.func = func
            h.name = func.__name__
            h.parent = self
            self.child_routers.append(h)
            return h

        return _register


def reply_only(*user_id, default=None):
    """user_idに指定されているユーザーIDからの
    メッセージにのみ返信させるデコレータ"""

    def _reply_only(router):
        router.reply_only += user_id
        router.default = default
        return router

    return _reply_only
