from funch.evaluator import FromTemplate
from pathlib import Path


current_dir = Path(__file__).parent
program_path = current_dir / "program.py"
n8_function_body_path = current_dir / "n8_function_body.txt"
with open(program_path) as f:
    template = f.read()


def test_score_evaluator():
    from_template = FromTemplate(template)
    score_evaluator = from_template.build_score_evaluator(tag="basic", input=8)

    function_body_plain = """    return 0"""

    with open(n8_function_body_path) as f:
        function_body_expert = f.read()

    assert score_evaluator(function_body_plain) == 256
    assert score_evaluator(function_body_expert) == 512


def test_validate_checker():
    from_template = FromTemplate(template)
    validate_checker = from_template.build_validity_checker()

    function_body_plain = """    return 0"""
    function_body_wrong_return_type = """    return 'error'"""
    function_body_with_error = """    return undefined"""

    assert validate_checker(function_body_plain)
    assert not validate_checker(function_body_with_error)
    assert not validate_checker(function_body_wrong_return_type)


def test_score_evaluator_with_score_translation():
    template_extended = (
        template + "\n\n@funch.score('basic')\ndef score(x):\n    return -x\n"
    )
    from_template = FromTemplate(template_extended)
    score_evaluator = from_template.build_score_evaluator(tag="basic", input=8)

    function_body_plain = """    return 0"""
    assert score_evaluator(function_body_plain) == -256
