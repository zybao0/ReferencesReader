from ReferencesReader import ReferencesReader

reader = ReferencesReader(r'./PDF_data','[0075] [Technical Report 2006] The Landscape of Parallel Computing Research- A View from Berkeley.pdf')
print(reader.min_y,reader.max_y)
#print(reader)