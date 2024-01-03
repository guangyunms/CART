import re
s=840#要改成test的数据量
with open('./PHO/model3/rec_success_record-askModel-3-pho-20231229.txt', 'r') as file:
    sum_Turn=0
    sum_H1=0
    sum_H5=0
    sum_H10=0
    sum_M1=0
    sum_M5=0
    sum_M10=0
    lines = file.readlines()
    for line in lines:
        # s+=1
        # 去掉字符串第一个和最后一个字符，即去掉“[]”
        line = line[1:-2]
        # print(line)
        tokens = re.split(r',', line.strip())
        # print(tokens)
        sum_Turn+=float(tokens[0])
        sum_H1+=float(tokens[1])
        sum_H5+=float(tokens[2])
        sum_H10+=float(tokens[3])
        sum_M1+=float(tokens[4])
        sum_M5+=float(tokens[5])
        sum_M10+=float(tokens[6])
print(sum_Turn/s)
print(sum_H1/s)
print(sum_H5/s)
print(sum_H10/s)
print(sum_M1/s)
print(sum_M5/s)
print(sum_M10/s)