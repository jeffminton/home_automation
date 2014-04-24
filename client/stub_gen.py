import xml.etree.ElementTree as ET
import pprint
import argparse
import subprocess



def print_struct_members( types, structs, fields, struct_elem, sub_types ):
    out = "\t" * sub_types
    print out + "\t" + struct_elem.tag + ": " + str( struct_elem.attrib )
    members = struct_elem.attrib["members"].split()
    for member in members:
        if member in types:
            print_sub_types( types, structs, fields, types[member], sub_types + 1 )
        elif member in fields:
            print_sub_types( types, structs, fields, fields[member], sub_types + 1 )
        elif member in structs:
            print_struct_members( types, structs, fields, structs[member], sub_types + 1 )

def print_sub_types( types, structs, fields, type_elem, sub_types ):
    
    out = '\t' * sub_types
    print out + "\t" + type_elem.tag + ": " + str( type_elem.attrib )
    if "type" in type_elem.attrib:
        if type_elem.attrib["type"] in types:
            print_sub_types( types, structs, fields, types[type_elem.attrib["type"]], sub_types + 1 )
        elif type_elem.attrib["type"] in structs:
            print_struct_members( types, structs, fields, structs[type_elem.attrib["type"]], sub_types + 1 )

def add_tab( tab_level ):
    return ( ' ' * ( tab_level * 4 ) )


def get_c_num( num ):
    return int( num.strip( 'uUlL' ) )

def get_type( types, type_id, type_dict ):
    
    if type_id in types:
        sub_type = types[type_id]
    else:
        print "no valid type for id " + type_id + " found for argument"
        exit( 1 )
    
    if 'Point' in sub_type.tag:
        print "**********This thing is a pointer***************"
        print sub_type.tag

    if 'Array' in sub_type.tag:
        type_dict['array'] = {}
        type_dict['array']['size'] = get_c_num( sub_type.attrib['max'] ) + 1

    #print sub_type.attrib
    if( 'name' not in sub_type.attrib or 'FundamentalType' not in sub_type.tag ) and \
    'Struct' not in sub_type.tag and 'Enumeration' not in sub_type.tag:
        return get_type( types, sub_type.attrib['type'], type_dict )
    else:
        return ( sub_type, type_dict )


def gen_var_dec( i, tab_level_cpp, types, local_vars, arg ):
    if 'name' in arg.attrib:
        arg_name = arg.attrib['name']
    else:
        arg_name = 'input_' + str( i )
    if arg_name not in local_vars:
        ( arg_type, type_dict ) = get_type( types, arg.attrib['type'], {} )
        local_vars[arg_name] = type_dict
        arg_type_name = arg_type.attrib['name']
        local_vars[arg_name]['tag'] = arg_type.tag
        local_vars[arg_name]['type'] = arg_type_name
        local_vars[arg_name]['type_elem'] = arg_type
        print arg_type_name
        if 'array' in local_vars[arg_name]:
            array_text = '[' + str( local_vars[arg_name]['array']['size'] ) + ']'
        else:
            array_text = ''
        local_vars[arg_name]['dec'] = add_tab( tab_level_cpp ) + arg_type_name + ' ' + arg_name + array_text + ';\n'

    return( arg_name, local_vars )



def expand_structs( header, tab_level_cpp, types, fields, local_vars, this_struct, function_def_cpp ):
    function_def_cpp += add_tab( tab_level_cpp ) + '//Declare all member of struct type ' + this_struct.attrib['name'] + '\n'
    members = this_struct.attrib['members'].split()
    for i, member in enumerate( members ):
        if member in types:
            arg = types[member]
            ( arg_name, local_vars ) = gen_var_dec( i, tab_level_cpp, types, local_vars, arg )
            if local_vars[arg_name]['dec'] not in function_def_cpp:
                function_def_cpp += local_vars[arg_name]['dec']

    return( local_vars, function_def_cpp )



def write_functions( module, header, types, fields, functions, header_lines ):

    tab_level_py = 1
    tab_level_cpp = 0

    overload_map = {}
    function_args = {}

    for function in functions:
        if function.attrib['name'] not in overload_map:
            overload_map[function.attrib['name']] = []
        overload_map[function.attrib['name']].append( function )

    for function_name in overload_map.keys():
        function_def_cpp = 'void ' + function_name + '_rpc( aJsonObject *params )\n'
        if function_def_cpp not in header_lines:
            local_vars = {}
            function_list = overload_map[function_name]
            header_lines.append( function_def_cpp )
            function_def_cpp += '{\n'
            tab_level_cpp += 1
            #declare types for all possible overloads
            overloaded = True if len( function_list ) > 1 else False
            for function in function_list:
                function_def_py = add_tab( tab_level_py ) + 'def ' + function_name + '( self' 
                #print function_name
                for i, arg in enumerate( function ):
                    ( arg_name, local_vars ) = gen_var_dec( i, tab_level_cpp, types, local_vars, arg )
                    function_def_cpp += local_vars[arg_name]['dec']
                    function_def_py += ', ' + arg_name
                    if 'Struct' in local_vars[arg_name]['tag']:
                        ( local_vars, function_def_cpp ) = expand_structs(  header, tab_level_cpp, types, fields, \
                        local_vars, local_vars[arg_name]['type_elem'], function_def_cpp )
                function_def_py += ' ):'
                for arg_name in local_vars:
                    json_type = add_tab( tab_level_cpp ) + 'aJsonObject* ' + arg_name + 'Param = aJson.getObjectItem(params, "' + arg_name + '");\n'
                    function_def_cpp += json_type
    
            function_def_cpp += '}\n'
            tab_level_cpp -= 1
            print function_def_cpp + '\n\n\n'
            print function_def_py + '\n\n\n'
            module.write( function_def_py + '\n\n\n' )
            header.write( function_def_cpp + '\n\n\n' )



def parse_c( file_name, sketch_name ):

    build = open( file_name, 'r' )
    sketch_name = ( sketch_name.partition( '.ino' ) )[0]

    build_cmd = build.readline()
    while( 'avr-g++' not in build_cmd ):
        build_cmd = build.readline()

    build_cmd_arr = build_cmd.split()

    xml_args = ''
    xml_gpp = ''
    xml_name = sketch_name + '_cpp.xml'

    for elem, arg in enumerate( build_cmd_arr ):
        if 'avr-g++' in arg:
            xml_gpp = arg
        if 'avr-' not in arg and '-c' not in arg:
            if '-o' in build_cmd_arr[ elem + 1 ]:
                in_file = arg
                break
            xml_args += arg + ' '

    xml_args = xml_args.strip()
    
    out_file = '-fxml=' + xml_name

    xml_cmd = ['gccxml', '-v', '--debug', '--gccxml-compiler', '"' + xml_gpp + '"', '--gccxml-cxxflags', '"' + xml_args + '"', in_file, out_file]

    xml_cmd_str = ''
    for arg in xml_cmd:
        xml_cmd_str += arg + ' '

    try:
        subprocess.check_call( xml_cmd_str, shell=True )
    except subprocess.CalledProcessError as e:
        print e.returncode
        print e.cmd
        exit( 1 )

    return xml_name


def parse_xml( sketch_name, xml_name ): 

    sketch_name = ( sketch_name.partition( '.ino' ) )[0]
    tree = ET.parse( xml_name ) 

    root = tree.getroot()

    filename_text = ["Arduino.h", "client"]
    tags = {}
    header_ids = []
    types = {}
    structs = {}
    fields = {}
    functions = []


    for child in root:
        if child.tag not in tags:
            tags[child.tag] = []
        else:
            tags[child.tag].append( child )
        if child.tag == "File":
            for filename in filename_text:
                if filename in child.attrib["name"]:
                    header_ids.append( child.attrib["id"] )
                    #print child.attrib
        if "Type" in child.tag or "Struct" in child.tag or "Field" in child.tag or "Enum" in child.tag:
            types[child.attrib["id"]] = child
        if "Struct" in child.tag:
            structs[child.attrib["id"]] = child
        if "Field" in child.tag:
            fields[child.attrib["id"]] = child

    print tags.keys()

    for child in root:
        if child.tag == "Function" and "__" not in child.attrib["name"] and child.attrib["file"] in header_ids and 'attach' not in child.attrib['name']:
            functions.append( child )
            #print child.tag, child.attrib["name"]
            #for params in child:
                #print params.tag, params.attrib

    '''
    for type_key in types.keys():
        print type_key + ": "
        print "\t" + str( types[type_key].attrib )

    for struct_key in structs.keys():
        print struct_key + ": "
        print "\t" + str( structs[struct_key].attrib )

    for function in functions:
        print function.attrib["name"] + ': ' + str( function.attrib )
        for arg in function:
            print_sub_types( types, structs, fields, arg, 1 )
    '''

    header = open( sketch_name + '.h', 'r+' )
    module = open( sketch_name + '.py', 'w' )

    header_lines = header.readlines()

    py_class_def = 'import RF22\n\n\n\n'
    py_class_def += 'class ' + sketch_name + ':\n\n'
    module.write( py_class_def )

    write_functions( module, header, types, fields, functions, header_lines )



def main():

    parser = argparse.ArgumentParser(description='Generate RPC stub code')
    parser.add_argument( '-f', '--file', help='The filname of the output from building in arduino ide' )
    parser.add_argument( '-i', '--ino', help='the name of the arduino sketch' )
    args = parser.parse_args()

    xml_name = parse_c( args.file, args.ino )

    parse_xml( args.ino, xml_name )




if __name__ == "__main__":
    main()
