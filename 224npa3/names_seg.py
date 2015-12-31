set_male_only_names = set()
set_female_only_names = set()

with open('baby_names.dat', 'r') as f:
	content = f.readlines()
	for line in content:
		fields = line.split()
		name = fields[1].lower()
		gender = fields[3].lower()
		if name not in set_male_only_names and name not in set_female_only_names:
			if gender=='boy':
				set_male_only_names.add(name)
			else:
				set_female_only_names.add(name)
		elif name in set_male_only_names:
			if gender=='girl':
				set_male_only_names.remove(name)
		elif name in set_female_only_names:
			if gender=='boy':
				set_female_only_names.remove(name)

print ','.join([name for name in set_male_only_names])
print ','.join([name for name in set_female_only_names])

