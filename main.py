import itertools
import csv
from operator import itemgetter
import sys

#============================================
# Helper functions for parsing NYC jobs data
#============================================
def parse_requirements(data):
    requirements = []
    if 'license' in data.lower():
        requirements.append('license')
    if 'master' in data.lower():
        requirements.append('master')
    elif 'baccalaureate' in data.lower() or 'bachelor' in data.lower():
        requirements.append('bachelor')
    elif 'high school' in data.lower():
        requirements.append('high school')
    elif 'associate degree' in data.lower() or "associate's degree" in data.lower():
        requirements.append('associate')
    return requirements

def salary_buckets(salary_from, salary_to, frequency):
    average = (int(salary_from) + int(salary_to))/2.0
    total_salary = average

    if frequency == 'Hourly':
        total_salary = average * 8 * 260
    elif frequency == 'Daily':
        total_salary = average * 260

    if total_salary < 25000:
        return "$0-$25,000"
    elif total_salary < 50000:
        return "$25,000-$50,000"
    elif total_salary < 75000:
        return "$50,000-$75,000"
    else:
        return "$100,000+"

#========================================
# Helper functions for apriori algorithm
#========================================
def subset_count(data, subset):
    count = 0
    for row in data:
        if set(subset).issubset(row):
            count+=1
    return count

def other_sets(relevant_items, element):
    other = []
    for ele in relevant_items:
        item = ele[0]
        if item != element:
            other.append(item)

    return other

def form_supersets(relevant_items):
    superset = set()
    all_same = True
    for ele in relevant_items:
        item = ele[0]
        for oset in other_sets(relevant_items, item):
            for index in range(len(item)-1):
                if oset[index] != item[index]:
                    all_same = False
            if all_same and item[-1] != oset[-1]:
                superset.add(tuple(set(item + oset)))
            all_same = True
    return superset

def groupings(dataset):
    subsets = []
    for size in range(1, len(dataset)):
        subsets += itertools.combinations(dataset, size)
    return set(subsets)

def confidence(data, lhs, rhs):
    num_left = 0.0
    num_right = 0
    for row in data:
        if set(lhs).issubset(set(row)):
            num_left += 1
            if set(rhs).issubset(set(row)):
                num_right +=1
    return num_right / num_left

#=================================================================
# Apriori algorithm - takes in data and outputs relevant datasets
#=================================================================
def apriori_algorithm(data, min_supp):
    data_support = {}
    total_rows = len(data) * 1.0
    for row in data:
        for element in set(row):
            cur_count = data_support.get(element)
            if cur_count:
                data_support[element] = cur_count+1
            else:
                data_support[element] = 1

    unique_keys = [ set([e]) for e in data_support.keys()]
    supersets = unique_keys
    datasets = []

    while True:
        relevant_items = []
        for key in supersets:
            support = subset_count(data, key) / total_rows
            if support >= min_supp:
                relevant_items.append((list(key), support))
        if relevant_items == []:
            break
        else:
            datasets.append(relevant_items)
        supersets = form_supersets(relevant_items)

    return datasets

#====================
# Main program logic
#====================
if len(sys.argv) == 4:

    filename = sys.argv[1]
    min_supp = float(sys.argv[2])
    min_conf = float(sys.argv[3])

    #===============================================
    # Parse relevant information from NYC jobs data
    #===============================================
    nyc_data = []
    cleaned_nyc_data = []

    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            nyc_data.append(row)

            agency = row[1]
            qualifications = row[14]
            salary_range_from = row[8]
            salary_range_to = row[9]
            salary_frequency = row[10]

            try: 
                entry = []
                entry.append(agency)
                entry += parse_requirements(qualifications)
                entry.append(salary_buckets(salary_range_from, salary_range_to, salary_frequency))
                cleaned_nyc_data.append(entry)
            except:
                pass

    #===========================================================================================
    # Given minimum support and confidence, write itemsets and association rules to output file
    #===========================================================================================
    input_data = cleaned_nyc_data
    apriori_passes = apriori_algorithm(input_data, min_supp)
    assoc_rules = set()

    itemsets = []
    for ap in apriori_passes[1:]:
        for itemset in ap:
            itemsets.append(itemset)
            possible_left = groupings(itemset[0])
            for left in possible_left:
                possible_right = set(itemset[0]).difference(set(left))
                if possible_right:
                    assoc_rules.add((left, tuple(possible_right), confidence(input_data, left, tuple(possible_right)), itemset[1]))

    output_file = open('output.txt', 'w')
    output_file.write('===================================\n')
    output_file.write(' Frequent itemsets (min_supp=' + str(min_supp * 100) + '%)\n')
    output_file.write('===================================\n')
    for itemset in sorted(itemsets, key=itemgetter(1), reverse=True):
        output_file.write(str(itemset[0]) + ', ' + str(round((itemset[1] * 100),3)) + '%\n')

    output_file.write('\n====================================================\n')
    output_file.write(' High-confidence association rules (min_conf=' + str(min_conf * 100) + '%)\n')
    output_file.write('====================================================\n')
    for assoc_rule in sorted(list(assoc_rules), key=itemgetter(2), reverse=True):
        if assoc_rule[2] >= min_conf:
            output_file.write(str(list(assoc_rule[0])) + ' => ' + str(list(assoc_rule[1])) + ' (Conf: ' + str(round((assoc_rule[2] * 100),3)) + '%, Supp: ' + str(round((assoc_rule[3] * 100),3)) + '%)\n')

else:
    print 'Usage: python main.py <INPUT_DATA_FILE> <MIN_SUPP> <MIN_CONF>'
