#!/usr/bin/python
#title           :extract_module_information.py 
#author          :Bala
#date            :May-9-2017
#version         :1.0
#usage           :python program.py 
#notes           :Extracts module information from OSG Connect submit host and combine with the module description. 
#python_version  :2.7

import os
import collections
import subprocess

def generate_listfile():
    """ Find the available modules on osg connect"""
    listfile = "1.tmp.out.dat"
    subprocess.call('module spider &> 1.tmp.out', shell=True, executable='/bin/bash')
    module_querry_cmd = "sed '/----/,/----/D' 1.tmp.out|sed '/^$/d' > {0}".format(listfile)
    subprocess.call(module_querry_cmd, shell=True, executable='/bin/bash')
    return listfile

def generate_module_name_version(data_listfile):
    """ From the data_listfile, extract the name of the module and versions"""
    module_inventory  = dict()
    with open(data_listfile,'r') as f:
        for line in f:
            line.rstrip()
            line_split = line.split(":")
            module_name = line_split[0].replace(" ","")  
            module_version = line_split[1].replace(module_name,"").replace(" ","").replace("/","").rstrip()
            if module_version:
                module_inventory[module_name] = module_version
            else:
                module_inventory[module_name] = "-"
   
    return module_inventory

def generate_module_description(module_name):
    """ For each module, get the description"""
    module_querry_cmd = "module whatis {0} &> 2.tmp.out".format(module_name)
    subprocess.call(module_querry_cmd, shell=True, executable='/bin/bash')
    module_description = "None"
    with open('2.tmp.out','r') as f:
        for line in f:
            if module_name in line and ":" in line:
                line_split = line.split(":")
                module_description = line_split[1].rstrip()
    return module_description

def get_modulenames_from_db(modules_db_file):
    """ Get module description from the supplied db file   """
    module_db_inventory  = dict()
    module_description = "none"
    module_tag = "none"
    with open(modules_db_file) as f:
        for line in f:
            new_line = line.rstrip()
            line_split = new_line.split("::")
            if(len(line_split) > 2):
                module_name = line_split[0].replace(" ","")
                module_description = line_split[1]
                module_tag = line_split[2]
                value = [module_description, module_tag]
                module_db_inventory[module_name] = value 
    return module_db_inventory

def get_ignored_module_names(ignore_file):
    module_names_ignored = []
    with open(ignore_file) as f:
        for line in f:
            new_line = line.rstrip().replace(" ","")
            module_names_ignored.append(new_line)
    return module_names_ignored

def find_diff_between_db_and_oasis(x, y, ignore_list):
    """ Get the difference between the supplied list of modules   """
    xu = [xe.upper() for xe in x]
    yu = [ye.upper() for ye in y]
    igu = [ige.upper() for ige in ignore_list]
    diff = list(set(xu).symmetric_difference(set(yu))) 
    for val in igu:
        diff.remove(val)
    return diff

def update_module_description_info(refdb, existmods):
    """ Update the information from the supplied db to the existing modules """
    module_list = []
    for key1, val1 in existmods.items():
        key1u = key1.upper()
        for key2, val2 in refdb.items():
            key2u = key2.upper()
            module_string = ""
            if key1u  == key2u:
               module_string = module_string + key1u + "  ::"  + "version (" + val1 + ")"  + "::"
               #module_string = module_string + keyu + "  ::"  
               for line in val2:
                   module_string = module_string + line  + "::"
               #print module_string
               module_list.append(module_string)
    return module_list

def get_module_info_arranged_by_tags(tag, module_info):
    """ Split the modules by the field of science based on tag """
    filtered_modules = []
    if tag == "tag0":
        filtered_modules.append('## Physics and Engineering ')
    if tag == "tag1":
        filtered_modules.append('## Chemistry and Biochemistry ')
    if tag == "tag2":
        filtered_modules.append('## Image Analysis ')
    if tag == "tag3":
        filtered_modules.append('## Bioinformatics ')
    if tag == "tag4":
        filtered_modules.append('## Numerical Libraries ')
    if tag == "tag5":
        filtered_modules.append('## Software Libraries, Languages, and Tools ')
    for line in module_info:
        if tag in line:
           filtered_modules.append(line) 
    filtered_modules.sort()
    return filtered_modules

def order_modules_by_tag(tags):
    """  Order the module names for each tag  """
    module_ordered = []
    tag_count = dict()
    for tag in tags:
        module_info_by_tag = get_module_info_arranged_by_tags(tag,updated_module_info)
        tag_count[tag] = -1
        for line in module_info_by_tag:
            module_ordered.append(line)
            tag_count[tag] += 1
        module_ordered.append(" ")
    return module_ordered, tag_count


def write_markdown_file(module_list, outputfile):
    """  Write the md file  """
    with open(outputfile,'w') as f:
         f.write('[title]: - "Software modules catalog"')
         f.write('\n')
         f.write('\n')
         f.write('[TOC]')
         f.write('\n')
         f.write('\n')
         for line in module_list:
             new_line = line.rstrip()
             line_split = new_line.split("::")
             if len(line_split) == 1:
                 f.write('\n')
                 f.write(new_line)
                 f.write('\n')
             if len(line_split) > 1:
                 key = "* **"+line_split[0].replace(" ","")+"**  "
                 ver = line_split[1] + " &mdash;  "
                 des = line_split[2]
                 mod_line = key + ver + des
                 f.write(mod_line)
                 f.write('\n')

def print_modules_summary_stats(diff_mods, tag_count):
    total_mods = 0
    for key, val in tag_count.items():
        print key, val
        total_mods += val
    print "="*60
    print  "total modules= ", total_mods
    print "="*60
    for line in diff_mods:
       print "missing module in module_db.data= ", line
    print "="*60
    print "Number of Missing Modules= ", len(diff_mods) 


if __name__ == '__main__':
    """ Extract the name of the module and versions from the submit host using module command. Pull the module information from module_db.dat. Combine these two information and write as an md file   """
    module_list_file = generate_listfile()
    modules_versions = generate_module_name_version(module_list_file)
    moduledb = get_modulenames_from_db("module_db.data")
    ignored_modules  = get_ignored_module_names("modules_ignore_list.data")
    diff_db_oasis =  find_diff_between_db_and_oasis(moduledb.keys(), modules_versions.keys(), ignored_modules)
    updated_module_info = update_module_description_info(moduledb,modules_versions)
    existing_tags = ('tag0', 'tag1', 'tag2', 'tag3', 'tag4', 'tag5')
    module_info_in_tagorder, tag_count  = order_modules_by_tag(existing_tags)
    output_md_file = "alpha_list.md"
    write_markdown_file(module_info_in_tagorder, output_md_file)
    print_modules_summary_stats(diff_db_oasis, tag_count)


