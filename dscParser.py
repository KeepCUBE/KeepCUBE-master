def parse_dsc(dsc):
    if dsc.startswith("#") and dsc.endswith(";") and dsc[1].isupper() and dsc[2].isupper() and dsc[3].isupper():
        head = dsc[1:4]
        body = dsc[4:-1]
        buffer = ""
        params = {}
        in_param = False
        in_string = False
        in_escape = False
        for c in body:
            if c.isupper() and not in_param:
                in_param = c
                buffer = ""
            elif in_escape:
                buffer += c
                in_escape = False
            elif c == '&' and not in_escape:
                in_string = not in_string
            elif in_string and c == '\\':
                if not in_escape:
                    in_escape = True
            elif (in_param and not c.isupper()) or (in_param and in_string):
                buffer += c
            elif (in_param and c.isupper() and not in_string):
                params[in_param] = buffer
                buffer = ""
                in_param = c
        params[in_param] = buffer
        command = {'head': head, 'body':params}
        return command
    else:
        return False