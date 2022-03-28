from ReferencesReader import ReferencesReader

reader = ReferencesReader(r'./PDF_data','[0075] [Technical Report 2006] The Landscape of Parallel Computing Research- A View from Berkeley.pdf')
reader.get_body()
print(reader.min_y,reader.max_y)
reader.find_references()
reader.split_references()