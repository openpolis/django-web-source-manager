from django_rq import job


@job
def verify_contents(contents):
    from websourcemonitor.services.playwright import PlaywrightWrapper

    pw = PlaywrightWrapper()
    results = []
    for obj in contents:
        results.append(
            (obj.url, obj.verify(playwright_wrapper=pw))
        )
    pw.stop()
    return results


@job
def update_contents(contents):
    from websourcemonitor.services.playwright import PlaywrightWrapper

    pw = PlaywrightWrapper()
    results = []
    for obj in contents:
        res = obj.url, obj.update(playwright_wrapper=pw)
        results.append(res)
    pw.stop()
    return results


def say_hello(name="world"):
    msg = f"Hello, {name}!"
    print(msg)
    return msg
