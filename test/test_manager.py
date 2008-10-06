import os, time, cStringIO
import libpry
import libqtile
import utils

class TestConfig(libqtile.config.Config):
    groups = ["a", "b", "c", "d"]
    layouts = [
                libqtile.layout.Stack(stacks=1, borderWidth=10),
                libqtile.layout.Stack(2, borderWidth=10)
            ]
    keys = [
        libqtile.manager.Key(
            ["control"],
            "k",
            libqtile.command._Call([("layout", None)], "up")
        ),
        libqtile.manager.Key(
            ["control"],
            "j",
            libqtile.command._Call([("layout", None)], "down")
        ),
    ]
    screens = [libqtile.manager.Screen(
            bottom=libqtile.bar.Bar(
                        [
                            libqtile.bar.GroupBox(),
                        ],
                        20
                    ),
    )]


class uMultiScreen(utils.QTileTests):
    config = TestConfig()
    def test_to_screen(self):
        assert self.c.screen.info()["index"] == 0
        self.c.to_screen(1)
        assert self.c.screen.info()["index"] == 1
        self.testWindow("one")
        self.c.to_screen(0)
        self.testWindow("two")

        ga = self.c.groups()["a"]
        assert ga["windows"] == ["two"]

        gb = self.c.groups()["b"]
        assert gb["windows"] == ["one"]

    def test_togroup(self):
        self.testWindow("one")
        libpry.raises("no such group", self.c.window.togroup, "nonexistent")
        assert self.c.groups()["a"]["focus"] == "one"
        self.c.window.togroup("a")
        assert self.c.groups()["a"]["focus"] == "one"
        self.c.window.togroup("b")
        assert self.c.groups()["b"]["focus"] == "one"
        assert self.c.groups()["a"]["focus"] == None
        self.c.to_screen(1)
        self.c.window.togroup("c")
        assert self.c.groups()["c"]["focus"] == "one"


class uSingle(utils.QTileTests):
    """
        We don't care if these tests run in a Xinerama or non-Xinerama X, and
        they only have to run under one of the two.
    """
    config = TestConfig()
    def test_events(self):
        assert self.c.status() == "OK"

    def test_report(self):
        p = os.path.join(self["tmpdir"], "crashreport")
        self.c.report("msg", p)
        assert os.path.isfile(p)
        self.c.report("msg", p)
        assert os.path.isfile(p + ".0")

    def test_keypress(self):
        self.testWindow("one")
        self.testWindow("two")
        v = self.c.simulate_keypress(["unknown"], "j")
        assert v.startswith("Unknown modifier")
        assert self.c.groups()["a"]["focus"] == "two"
        self.c.simulate_keypress(["control"], "j")
        assert self.c.groups()["a"]["focus"] == "one"

    def test_spawn(self):
        assert self.c.spawn("true") == None

    def test_kill(self):
        self.testWindow("one")
        self.testwindows = []
        self.c.window[self.c.window.info()["id"]].kill()
        self.c.sync()
        for i in range(20):
            if len(self.c.windows()) == 0:
                break
            time.sleep(0.1)
        else:
            raise AssertionError("Window did not die...")

    def test_regression_groupswitch(self):
        self.c.group["c"].toscreen()
        self.c.group["d"].toscreen()
        assert self.c.groups()["c"]["screen"] == None

    def test_nextlayout(self):
        self.testWindow("one")
        self.testWindow("two")
        assert len(self.c.layout.info()["stacks"]) == 1
        self.c.nextlayout()
        assert len(self.c.layout.info()["stacks"]) == 2
        self.c.nextlayout()
        assert len(self.c.layout.info()["stacks"]) == 1

    def test_log_clear(self):
        self.testWindow("one")
        self.c.log_clear()
        assert len(self.c.log()) == 1

    def test_log_length(self):
        self.c.log_setlength(5)
        assert self.c.log_getlength() == 5

    def test_inspect(self):
        self.testWindow("one")
        assert self.c.window.inspect()


class uQTile(utils.QTileTests):
    """
        These tests should run in both Xinerama and non-Xinerama modes.
    """
    config = TestConfig()
    def test_mapRequest(self):
        self.testWindow("one")
        info = self.c.groups()["a"]
        assert "one" in info["windows"]
        assert info["focus"] == "one"

        self.testWindow("two")
        info = self.c.groups()["a"]
        assert "two" in info["windows"]
        assert info["focus"] == "two"

    def test_unmap(self):
        one = self.testWindow("one")
        two = self.testWindow("two")
        three = self.testWindow("three")
        info = self.c.groups()["a"]
        assert info["focus"] == "three"

        assert len(self.c.windows()) == 3
        self.kill(three)

        assert len(self.c.windows()) == 2
        info = self.c.groups()["a"]
        assert info["focus"] == "two"

        self.kill(two)
        assert len(self.c.windows()) == 1
        info = self.c.groups()["a"]
        assert info["focus"] == "one"

        self.kill(one)
        assert len(self.c.windows()) == 0
        info = self.c.groups()["a"]
        assert info["focus"] == None

    def test_setgroup(self):
        self.testWindow("one")
        self.c.group["b"].toscreen()
        self._groupconsistency()
        if len(self.c.screens()) == 1:
            assert self.c.groups()["a"]["screen"] == None
        else:
            assert self.c.groups()["a"]["screen"] == 1
        assert self.c.groups()["b"]["screen"] == 0
        self.c.group["c"].toscreen()
        self._groupconsistency()
        assert self.c.groups()["c"]["screen"] == 0

    def test_unmap_noscreen(self):
        self.testWindow("one")
        pid = self.testWindow("two")
        assert len(self.c.windows()) == 2
        self.c.group["c"].toscreen()
        self._groupconsistency()
        self.c.status()
        assert len(self.c.windows()) == 2
        self.kill(pid)
        assert len(self.c.windows()) == 1
        assert self.c.groups()["a"]["focus"] == "one"


class uKey(libpry.AutoTree):
    def test_init(self):
        libpry.raises(
            "unknown key",
            libqtile.manager.Key,
            [], "unknown", libqtile.command._Call("base", None, "foo")
        )
        libpry.raises(
            "unknown modifier",
            libqtile.manager.Key,
            ["unknown"], "x", libqtile.command._Call("base", None, "foo")
        )


class uLog(libpry.AutoTree):
    def test_all(self):
        io = cStringIO.StringIO()
        l = libqtile.manager.Log(5, io)
        for i in range(10):
            l.add(i)
        assert len(l.log) == 5
        assert l.log[0] == 5
        assert l.log[4] == 9

        l.write(io, "\t")
        assert "\t5" in io.getvalue()
        l.clear()
        assert not l.log

        l.setLength(5)
        assert l.length == 5

    def test_setLength(self):
        io = cStringIO.StringIO()
        l = libqtile.manager.Log(10, io)
        for i in range(10):
            l.add(i)
        assert l.length == 10
        assert len(l.log) == 10
        l.setLength(5)
        assert l.length == 5
        assert len(l.log) == 5
        assert l.log[-1] == 9
        


class TScreen(libqtile.manager.Screen):
    def setGroup(self, x): pass


class uScreenDimensions(libpry.AutoTree):
    def test_dx(self):
        s = TScreen(left = libqtile.bar.Gap(10))
        s._configure(None, 0, 0, 0, 100, 100, None, None)
        assert s.dx == 10

    def test_dwidth(self):
        s = TScreen(left = libqtile.bar.Gap(10))
        s._configure(None, 0, 0, 0, 100, 100, None, None)
        assert s.dwidth == 90
        s.right = libqtile.bar.Gap(10)
        assert s.dwidth == 80

    def test_dy(self):
        s = TScreen(top = libqtile.bar.Gap(10))
        s._configure(None, 0, 0, 0, 100, 100, None, None)
        assert s.dy == 10

    def test_dheight(self):
        s = TScreen(top = libqtile.bar.Gap(10))
        s._configure(None, 0, 0, 0, 100, 100, None, None)
        assert s.dheight == 90
        s.bottom = libqtile.bar.Gap(10)
        assert s.dheight == 80


class uEvent(libpry.AutoTree):
    def test_subscribe(self):
        self.testVal = None
        def test(x):
            self.testVal = x
        class Dummy: pass
        dummy = Dummy()
        io = cStringIO.StringIO()
        dummy.log = libqtile.manager.Log(5, io)
        e = libqtile.manager.Event(dummy)
        libpry.raises("unknown event", e.subscribe, "unkown", test)
        libpry.raises("unknown event", e.fire, "unkown")
        e.subscribe("window_add", test)
        e.fire("window_add", 1)
        assert self.testVal == 1


tests = [
    utils.XNest(xinerama=True), [
        uQTile(),
        uMultiScreen()
    ],
    utils.XNest(xinerama=False), [
        uSingle(),
        uQTile()
    ],
    uKey(),
    uLog(),
    uScreenDimensions(),
    uEvent(),
]

