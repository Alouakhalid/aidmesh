from server.jobs import JobStore
from server.limits import RateLimiter


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_limiter_per_client_and_window():
    clock = Clock()
    rl = RateLimiter(per_ip=2, per_day=100, clock=clock)
    assert rl.allow("a") and rl.allow("a")
    assert not rl.allow("a")
    assert rl.allow("b")  # other clients are independent
    clock.t += 3601
    assert rl.allow("a")  # the hour window slid past


def test_limiter_global_daily_cap_and_reset():
    clock = Clock()
    rl = RateLimiter(per_ip=10, per_day=3, clock=clock)
    assert [rl.allow(c) for c in "abcd"] == [True, True, True, False]
    clock.t += 86401
    assert rl.allow("d")
    rl.reset()
    assert rl.allow("a")


def test_limiter_rejected_hit_is_not_recorded():
    rl = RateLimiter(per_ip=1, per_day=100, clock=Clock())
    assert rl.allow("a")
    assert not rl.allow("a") and not rl.allow("a")
    assert len(rl._day) == 1


def test_jobstore_active_cap_and_public_view():
    clock = Clock()
    store = JobStore(max_active=2, clock=clock)
    first, second = store.create(), store.create()
    assert first and second and store.create() is None
    store.update(first, status="done", result={"x": 1})
    assert store.public(first) == {"status": "done", "result": {"x": 1}}  # no internal timestamp
    assert store.create() is not None  # a finished job frees a slot
    assert store.public("missing") is None


def test_jobstore_expires_old_jobs():
    clock = Clock()
    store = JobStore(max_active=5, clock=clock)
    old = store.create()
    clock.t += 1801
    store.create()
    assert store.public(old) is None
