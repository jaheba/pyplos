from pyplos import ppl


def check_bool(query, result):
    data = [{}]

    assert len(ppl(f"where {query}", data)) == result


def check_eval(query):
    check_bool(
        query.replace("True", "1=1").replace("False", "1!=1"),
        eval(query.replace(" = ", " == ")),
    )


def test_comparison():
    check_eval("1 = 1")
    check_eval("1 = 2")

    check_eval("1 != 1")
    check_eval("1 != 2")

    check_eval("1 > 2")
    check_eval("2 > 2")
    check_eval("3 > 2")

    check_eval("1 >= 2")
    check_eval("2 >= 2")
    check_eval("3 >= 2")

    check_eval("1 < 2")
    check_eval("2 < 2")
    check_eval("3 < 2")

    check_eval("1 <= 2")
    check_eval("2 <= 2")
    check_eval("3 <= 2")


def test_or():
    check_eval("True or True")
    check_eval("True or False")
    check_eval("False or True")
    check_eval("False or False")


def test_or():
    check_eval("True and True")
    check_eval("True and False")
    check_eval("False and True")
    check_eval("False and False")


#     assert len(ppl("where 1 = 1 and 2 = 2", [{}])) == 1
#     assert len(ppl("where 1 != 1 and 2 = 2", [{}])) == 1
#     assert len(ppl("where 1 = 1 and 2 = 2", [{}])) == 1


# def test_or():
#     assert len(ppl("where 1 = 1 and 2 = 2", [{}])) == 1
