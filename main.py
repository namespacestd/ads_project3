import itertools
import csv
from operator import itemgetter

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
    for item in relevant_items:
        if item != element:
            other.append(item)

    return other

def form_supersets(relevant_items):
    superset = set()
    all_same = True
    for item in relevant_items:
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
            if (subset_count(data, key) / total_rows) >= min_supp:
                relevant_items.append(list(key))
        if relevant_items == []:
            break
        else:
            datasets.append(relevant_items)
        supersets = form_supersets(relevant_items)

    return datasets

#===============================================
# Parse relevant information from NYC jobs data
#===============================================
nyc_data = []
cleaned_nyc_data = []

with open('NYC_Jobs.csv', 'rb') as csvfile:
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

#===================================================================================
# Given minimum support and confidence, write datasets and relations to output file
#===================================================================================
min_supp = .05   
min_conf = .5

input_data = cleaned_nyc_data
apriori_passes = apriori_algorithm(input_data, min_supp)
relations = set()

for ap in apriori_passes[1:]:
    for ele in ap:
        possible_left = groupings(ele)
        for left in possible_left:
            possible_right = set(ele).difference(set(left))
            if possible_right:
                relations.add((left, tuple(possible_right), confidence(input_data, left, tuple(possible_right))))

for relation in sorted(list(relations), key=itemgetter(2), reverse=True):
    if relation[2] >= min_conf:
        print relation
