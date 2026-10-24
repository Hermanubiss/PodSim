from binder import vid_pid_from_guid


def test_vid_pid_from_xbox_360_guid():
    assert vid_pid_from_guid("030000005e0400008e02000000007200") == ("045E", "028E")


def test_vid_pid_from_vkb_guid():
    assert vid_pid_from_guid("030000001d2300000002000000000000") == ("231D", "0200")


def test_vid_pid_unknown_format():
    assert vid_pid_from_guid("05000000aabbccddeeff001122334455") == (None, None)
