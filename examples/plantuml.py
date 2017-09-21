#!/usr/bin/env python

"""
Pandoc filter to process code blocks with class "plantuml" into
plant-generated images.

Needs `plantuml.jar` from http://plantuml.com/.
"""

import os
import sys
from subprocess import call

from pandocfilters import toJSONFilter, Para, Image

#########################################################################
# backported helpers

# from pandocfilters import get_filename4code, get_caption, get_extension
import pandocfilters
# redirect names by defaulting to these if not in pandocfilters

def backport_get_filename4code(module, content, ext=None):
    """Generate filename based on content

    The function ensures that the (temporary) directory exists, so that the
    file can be written.

    Example:
        filename = get_filename4code("myfilter", code)
    """
    imagedir = module + "-images"
    import hashlib
    fn = hashlib.sha1(content.encode(sys.getfilesystemencoding())).hexdigest()
    try:
        os.mkdir(imagedir)
        sys.stderr.write('Created directory ' + imagedir + '\n')
    except OSError:
        pass
    if ext:
        fn += "." + ext
    return os.path.join(imagedir, fn)
get_filename4code = getattr(pandocfilters, "get_filename4code", backport_get_filename4code)

def backport_get_value(kv, key, value = None):
    """get value from the keyvalues (options)"""
    res = []
    for k, v in kv:
        if k == key:
            value = v
        else:
            res.append([k, v])
    return value, res
get_value = getattr(pandocfilters, "get_value", backport_get_value)

def backport_get_caption(kv):
    """get caption from the keyvalues (options)

    Example:
      if key == 'CodeBlock':
        [[ident, classes, keyvals], code] = value
        caption, typef, keyvals = get_caption(keyvals)
        ...
        return Para([Image([ident, [], keyvals], caption, [filename, typef])])
    """
    caption = []
    typef = ""
    from pandocfilters import Str
    value, res = get_value(kv, u"caption")
    if value is not None:
        caption = [Str(value)]
        typef = "fig:"

    return caption, typef, res
get_caption = getattr(pandocfilters, "get_caption", backport_get_caption)

def backport_get_extension(format, default, **alternates):
    """get the extension for the result, needs a default and some specialisations

    Example:
      filetype = get_extension(format, "png", html="svg", latex="eps")
    """
    try:
        return alternates[format]
    except KeyError:
        return default
get_extension = getattr(pandocfilters, "get_extension", backport_get_extension)

#########################################################################

def plantuml(key, value, format, _):
    if key == 'CodeBlock':
        [[ident, classes, keyvals], code] = value

        if "plantuml" in classes:
            caption, typef, keyvals = get_caption(keyvals)

            filename = get_filename4code("plantuml", code)
            filetype = get_extension(format, "png", html="svg", latex="eps")

            src = filename + '.uml'
            dest = filename + '.' + filetype

            if not os.path.isfile(dest):
                txt = code.encode(sys.getfilesystemencoding())
                if not txt.startswith("@start"):
                    txt = "@startuml\n" + txt + "\n@enduml\n"
                with open(src, "w") as f:
                    f.write(txt)

                call(["java", "-jar", "plantuml.jar", "-t"+filetype, src])
                sys.stderr.write('Created image ' + dest + '\n')

            return Para([Image(#[ident, [], keyvals],
                caption, [dest, typef])])

if __name__ == "__main__":
    toJSONFilter(plantuml)
