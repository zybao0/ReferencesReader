from ReferencesReader import ReferencesReader

reader = ReferencesReader(r'./PDF_data','[0057] [ACM 2008] Real-Time, All-Frequency Shadows in Dynamic Scenes.pdf')
print(reader.min_y,reader.max_y)
print(reader)