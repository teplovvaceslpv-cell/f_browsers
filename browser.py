import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import QIcon
import ua_generator
import os

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-features=DnsOverHttps "
    "--dns-over-https-mode=secure "
    "--dns-over-https-templates=https://dns.quad9.net/dns-query"
)


class BackButton(QToolButton):
    def __init__(self, parent=None):
        super(BackButton, self).__init__(parent)
        self.setIcon(QIcon("img/back.png"))
        self.setIconSize(QSize(24, 24))
        self.setToolTip("Назад")


class ForwardButton(QToolButton):
    def __init__(self, parent=None):
        super(ForwardButton, self).__init__(parent)
        self.setIcon(QIcon("img/forward.png"))
        self.setIconSize(QSize(24, 24))
        self.setToolTip("Вперед")


class ReloadButton(QToolButton):
    def __init__(self, parent=None):
        super(ReloadButton, self).__init__(parent)
        self.setIcon(QIcon("img/reload.png"))
        self.setIconSize(QSize(24, 24))
        self.setToolTip("Перезагрузить")


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.private_profile = QWebEngineProfile()
        self.private_profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        self.private_profile.setHttpCacheType(QWebEngineProfile.NoCache)
        self.private_profile.setSpellCheckEnabled(False)
        try:
            random_ua = ua_generator.generate(device='desktop')
            self.private_profile.setHttpUserAgent(random_ua.text)
            print(random_ua.text)
        except Exception:
            pass

        self.page = QWebEnginePage(self.private_profile, self)

        self.browser = QWebEngineView(self)
        self.browser.setPage(self.page)
        self.page.profile().downloadRequested.connect(self.save_file)
        settings = self.page.settings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebRTCPublicInterfacesOnly, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, False)
        settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, False)
        self.page.featurePermissionRequested.connect(self.reject_permissions)

        self.browser.createWindow = self._create_window

        spoof_js = """
        (function() {
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});

            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => []});
            Object.defineProperty(navigator, 'mimeTypes', {get: () => []});

            const noisify = (canvas, context) => {
                const shift = {
                    r: Math.floor(Math.random() * 10) - 5,
                    g: Math.floor(Math.random() * 10) - 5,
                    b: Math.floor(Math.random() * 10) - 5,
                    a: Math.floor(Math.random() * 10) - 5
                };
                const width = canvas.width, height = canvas.height;
                if (!width || !height) return;
                const imageData = context.getImageData(0, 0, width, height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i]     = imageData.data[i]     + shift.r;
                    imageData.data[i + 1] = imageData.data[i + 1] + shift.g;
                    imageData.data[i + 2] = imageData.data[i + 2] + shift.b;
                    imageData.data[i + 3] = imageData.data[i + 3] + shift.a;
                }
                context.putImageData(imageData, 0, 0);
            };

            const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(...args) {
                const ctx = this.getContext('2d');
                if (ctx) noisify(this, ctx);
                return origToDataURL.apply(this, args);
            };

            const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {
                const imageData = origGetImageData.apply(this, args);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] += Math.floor(Math.random() * 4) - 2;
                }
                return imageData;
            };

            const getParameterProxyHandler = {
                apply(target, ctx, args) {
                    const param = args[0];
                    if (param === 37445) return 'Intel Inc.';
                    if (param === 37446) return 'Intel Iris OpenGL Engine';
                    return Reflect.apply(target, ctx, args);
                }
            };
            if (window.WebGLRenderingContext) {
                WebGLRenderingContext.prototype.getParameter = new Proxy(
                    WebGLRenderingContext.prototype.getParameter, getParameterProxyHandler
                );
            }
            if (window.WebGL2RenderingContext) {
                WebGL2RenderingContext.prototype.getParameter = new Proxy(
                    WebGL2RenderingContext.prototype.getParameter, getParameterProxyHandler
                );
            }

            const origGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function(...args) {
                const data = origGetChannelData.apply(this, args);
                for (let i = 0; i < data.length; i += 100) {
                    data[i] = data[i] + (Math.random() * 0.0000001);
                }
                return data;
            };

            if (document.fonts && document.fonts.check) {
                const origCheck = document.fonts.check.bind(document.fonts);
                document.fonts.check = function(...args) {
                    return Math.random() > 0.5 ? origCheck(...args) : false;
                };
            }

            const origDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(...args) {
                if (args[1]) args[1].timeZone = 'UTC';
                return new origDateTimeFormat(...args);
            };
            Intl.DateTimeFormat.prototype = origDateTimeFormat.prototype;

            Date.prototype.getTimezoneOffset = function() { return 0; };

            Object.defineProperty(navigator, 'getBattery', {
                get: () => undefined,
                configurable: true,
                enumerable: true
            });

            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                navigator.mediaDevices.enumerateDevices = function() {
                    return Promise.resolve([]);
                };
            }
        })();
        """
        script = QWebEngineScript()
        script.setSourceCode(spoof_js)
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setWorldId(QWebEngineScript.MainWorld)
        self.page.scripts().insert(script)

        self.browser.setUrl(QUrl("https://duckduckgo.com/"))

        self.setCentralWidget(self.browser)

        navtb = QToolBar()
        self.addToolBar(navtb)

        back_btn = BackButton()
        back_btn.clicked.connect(self.browser.back)
        navtb.addWidget(back_btn)

        forward_btn = ForwardButton()
        forward_btn.clicked.connect(self.browser.forward)
        navtb.addWidget(forward_btn)

        reload_btn = ReloadButton()
        reload_btn.clicked.connect(self.browser.reload)
        navtb.addWidget(reload_btn)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        self.resize(1024, 768)
        self.show()

        self.browser.urlChanged.connect(self.update_urlbar)
        self.browser.loadFinished.connect(self.update_title)

    def _create_window(self, wintype):
        return self.browser

    def update_title(self):
        self.setWindowTitle("f_browsers")

    def navigate_to_url(self):
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme("https")
        self.browser.setUrl(q)

    def update_urlbar(self, q):
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def save_file(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", download.suggestedFileName())
        if path:
            download.setPath(path)
            download.accept()
        else:
            download.cancel()

    def reject_permissions(self, url, feature):
        self.page.setFeaturePermission(
            url, feature, QWebEnginePage.PermissionDeniedByUser
        )

    def closeEvent(self, event):
        self.private_profile.clearHttpCache()
        self.private_profile.cookieStore().deleteAllCookies()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec_()
