from pythoscope.generator.lines import *
from pythoscope.generator.code_string import addimport, CodeString, combine,\
    putinto
from pythoscope.generator.constructor import constructor_as_string,\
    call_as_string_for, type_as_string, todo_value
from pythoscope.generator.method_call_context import MethodCallContext
from pythoscope.generator.objects_namer import Assign

from pythoscope.serializer import SerializedObject, is_serialized_string
from pythoscope.side_effect import BuiltinMethodWithPositionArgsSideEffect,\
    AttributeRebind
from pythoscope.store import GeneratorObject, Call, Method
from pythoscope.util import assert_argument_type


class Template(object):
    # :: (CodeString, CodeString) -> CodeString
    def equal_assertion(self, expected, actual):
        raise NotImplementedError("Method equal_assertion() not defined.")
    # :: (CodeString, CodeString) -> CodeString
    def raises_assertion(self, exception, call):
        raise NotImplementedError("Method raises_assertion() not defined.")
    # :: () -> CodeString
    def skip_test(self):
        raise NotImplementedError("Method skip_test() not defined.")

class UnittestTemplate(Template):
    def equal_assertion(self, expected, actual):
        return combine(expected, actual, "self.assertEqual(%s, %s)")
    def raises_assertion(self, exception, call):
        return combine(exception, call, "self.assertRaises(%s, %s)")
    def skip_test(self):
        return CodeString("assert False  # implement your test here")

class NoseTemplate(Template):
    def equal_assertion(self, expected, actual):
        return addimport(combine(expected, actual, "assert_equal(%s, %s)"),
                         ('nose.tools', 'assert_equal'))
    def raises_assertion(self, exception, call):
        return addimport(combine(exception, call, "assert_raises(%s, %s)"),
                         ('nose.tools', 'assert_raises'))
    def skip_test(self):
        return addimport(CodeString("raise SkipTest # implement your test here"),
                         ('nose', 'SkipTest'))

# :: CodeString -> CodeString
def add_newline(code_string):
    return combine(code_string, "\n")

# :: CodeString -> CodeString
def map_types(string):
    return putinto(string, "map(type, %s)")

# :: CodeString -> CodeString
def type_of(string):
    return putinto(string, "type(%s)")

# :: CodeString -> CodeString
def in_lambda(string):
    return putinto(string, "lambda: %s")

# :: Definition -> (str, str)
def import_for(definition):
    if isinstance(definition, Method):
        return import_for(definition.klass)
    return (definition.module.locator, definition.name)

# :: (CodeString, CodeString, Template) -> CodeString
def equal_assertion_on_values_or_types(expected, actual, template):
    if expected.uncomplete:
        pass
    else:
        return template.equal_assertion(expected, actual)

def call_name(call, assigned_names):
    if isinstance(call, MethodCallContext):
        if call.call.definition.is_creational():
            return call.call.definition.klass.name
        return "%s.%s" % (assigned_names[call.user_object], call.call.definition.name)
    return call.definition.name

def call_in_test(call, already_assigned_names):
    if isinstance(call, GeneratorObject) or (isinstance(call, MethodCallContext) and isinstance(call.call, GeneratorObject)):
        callstring = call_as_string_for(call_name(call, already_assigned_names), call.args,
                                        call.definition, already_assigned_names)
        callstring = combine(callstring, str(len(call.calls)), template="list(islice(%s, %s))")
        callstring = addimport(callstring, ("itertools", "islice"))
    else:
        callstring = call_as_string_for(call_name(call, already_assigned_names), call.input,
                                        call.definition, already_assigned_names)
        callstring = addimport(callstring, import_for(call.definition))
    return callstring

# :: GeneratorObject -> [SerializedObject]
def generator_object_yields(gobject):
    assert_argument_type(gobject, (GeneratorObject, MethodCallContext))
    return [c.output for c in gobject.calls]

def code_string_from_module_variable_reference(ref):
    return CodeString("%s.%s" % (ref.module, ref.name), imports=set([ref.module]))

def code_string_from_object_attribute_reference(ref, assigned_names):
    return CodeString("%s.%s" % (assigned_names[ref.obj], ref.name))

def variable_assignment_line(left, right, already_assigned_names):
    if isinstance(right, ModuleVariableReference):
        constructor = code_string_from_module_variable_reference(right)
    elif isinstance(right, str):
        constructor = CodeString(right)
    elif isinstance(right, (Call, MethodCallContext)):
        constructor = call_in_test(right, already_assigned_names)
        # Associate the name with the call's output, not the call itself.
        already_assigned_names[right.output] = left
    else:
        constructor = constructor_as_string(right, already_assigned_names)
        already_assigned_names[right] = left
    return combine(left, constructor, "%s = %s")

def attribute_assignment_line(left, right, already_assigned_names):
    try:
        constructor = CodeString(already_assigned_names[right])
    except KeyError:
        constructor = constructor_as_string(right, already_assigned_names)
    return combine(left, constructor, "%s = %s")

# :: ([Event], Template) -> CodeString
def generate_test_contents(events, template):
    contents = CodeString("")
    all_uncomplete = False
    already_assigned_names = {}
    for event in events:
        if isinstance(event, Assign):
            line = variable_assignment_line(event.name, event.obj, already_assigned_names)
        elif isinstance(event, BindingChange):
            if event.name.obj in list(already_assigned_names.keys()):
                already_assigned_names[event.obj] = code_string_from_object_attribute_reference(event.name, already_assigned_names)
            continue # This is not a real test line, so just go directly to the next line.
        elif isinstance(event, EqualAssertionLine):
            expected = constructor_as_string(event.expected, already_assigned_names)
            if isinstance(event.actual, (Call, MethodCallContext)):
                actual = call_in_test(event.actual, already_assigned_names)
            elif isinstance(event.actual, ModuleVariableReference):
                actual = code_string_from_module_variable_reference(event.actual)
            elif isinstance(event.actual, ObjectAttributeReference):
                actual = code_string_from_object_attribute_reference(event.actual, already_assigned_names)
            elif isinstance(event.actual, str):
                actual = CodeString(event.actual)
            else:
                actual = constructor_as_string(event.actual, already_assigned_names)
            if expected.uncomplete:
                expected = type_as_string(event.expected)
                actual = type_of(actual)
            line = template.equal_assertion(expected, actual)
        elif isinstance(event, GeneratorAssertionLine):
            call = event.generator_call
            yields = generator_object_yields(call)
            expected = constructor_as_string(yields, already_assigned_names)
            actual = call_in_test(call, already_assigned_names)
            if expected.uncomplete:
                expected = type_as_string(yields)
                actual = map_types(actual)
                actual = addimport(actual, 'types')
            line = template.equal_assertion(expected, actual)
        elif isinstance(event, RaisesAssertionLine):
            actual = call_in_test(event.call, already_assigned_names)
            actual = in_lambda(actual)
            if is_serialized_string(event.expected_exception):
                exception = todo_value(event.expected_exception.reconstructor)
            else:
                exception = CodeString(event.expected_exception.type_name)
                exception = addimport(exception, event.expected_exception.type_import)
            line = template.raises_assertion(exception, actual)
        elif isinstance(event, CommentLine):
            line = CodeString(event.comment)
        elif isinstance(event, SkipTestLine):
            line = template.skip_test()
        elif isinstance(event, EqualAssertionStubLine):
            line = template.equal_assertion(CodeString('expected', uncomplete=True), event.actual)
        elif isinstance(event, BuiltinMethodWithPositionArgsSideEffect):
            # All objects affected by side effects are named.
            object_name = already_assigned_names[event.obj]
            line = call_as_string_for("%s.%s" % (object_name, event.definition.name),
                                      event.args_mapping(),
                                      event.definition,
                                      already_assigned_names)
        elif isinstance(event, AttributeRebind):
            # All objects affected by side effects are named.
            object_name = already_assigned_names[event.obj]
            line = attribute_assignment_line("%s.%s" % (object_name, event.name),
                                             event.value,
                                             already_assigned_names)

        else:
            raise TypeError("Don't know how to generate test contents for event %r." % event)
        if line.uncomplete:
            all_uncomplete = True
        if all_uncomplete and not isinstance(event, SkipTestLine):
            line = combine("# ", line)
        contents = combine(contents, add_newline(line))
    return contents
