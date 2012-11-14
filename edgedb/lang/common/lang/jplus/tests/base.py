##
# Copyright (c) 2012 Sprymix Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import subprocess
import tempfile

from metamagic.utils import resource
from metamagic.utils.markup import dump, dump_code

from .. import transpiler, parser

from metamagic.utils.debug import debug
from metamagic.utils.lang.javascript.tests import base as js_base_test
from metamagic.utils.lang.javascript.codegen import JavascriptSourceGenerator

from metamagic.utils.datastructures import OrderedSet


from metamagic.utils.lang.javascript import Loader as JSLoader, BaseJavaScriptModule, \
                                            Language as JSLanguage, JavaScriptModule, \
                                            VirtualJavaScriptResource


from metamagic.node.targets import Target


class BaseJPlusTestMeta(js_base_test.JSFunctionalTestMeta):
    doc_prefix = 'JS+'

    @classmethod
    @debug
    def do_test(mcls, source, name=None, data=None):
        source = source[len(mcls.doc_prefix)+1:]
        expected = ''

        if '%%' in source:
            source, expected = source.split('%%')
            expected = expected.strip()


        p = parser.Parser()
        jsp_ast = p.parse(source)

        """LOG [jsp] JS+ AST
        dump(jsp_ast)
        """

        t = transpiler.Transpiler()
        js_ast, js_deps = t.transpile(jsp_ast)

        """LOG [jsp] Resultant JS AST
        dump(js_ast)
        """

        all_deps = OrderedSet()
        for dep in js_deps:
            all_deps.update(Target.get_import_list((dep,)))

        """LOG [jsp] Resultant JS Deps
        dump(all_deps)
        """

        js_src = JavascriptSourceGenerator.to_source(js_ast)

        """LOG [jsp] Resultant JS Source
        dump_code(js_src, lexer='javascript', header='Resultant JS Source')
        """

        bootstrap = []
        for dep in all_deps:
            if isinstance(dep, JavaScriptModule):
                with open(dep.__file__, 'rt') as dep_f:
                    bootstrap.append(dep_f.read())
            elif (isinstance(dep, resource.VirtualFile) and
                                        isinstance(dep, BaseJavaScriptModule)):
                bootstrap.append(dep.__sx_resource_get_source__())

        with tempfile.NamedTemporaryFile('w') as file:
            file.write('(function() {\n\n');
            file.write('function print() { console.log.apply(console, arguments); };\n\n');
            file.write('\n\n'.join(bootstrap))
            file.write(js_src)
            file.write('\n\n}).call(global);'); #nodejs: to fix 'this' to point to the global ns
            file.flush()

            result = subprocess.getoutput('{} {}'.format(mcls.v8_executable, file.name))
            result = result.strip()

            if result != expected:
                """LOG [jsp] RESULT
                dump(result, header='RESULT', trim=False)
                """

                """LOG [jsp] EXPECTED
                dump(expected, header='EXPECTED', trim=False)
                """

            assert result == expected, result

class BaseJPlusTest(metaclass=BaseJPlusTestMeta):
    pass
