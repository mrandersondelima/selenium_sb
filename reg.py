import re

#qualquer palavra sub que pode ter um hífen ou não, seguido de um ou mais números

print( re.findall(r"sub-*\d+|reserv.*|femin.*|u-*\d+|women", "feminio".lower()) )

#print( re.findall(r"sub-*\d+", "Sub-23".lower()) )