from ReferencesReader import ReferencesReader

reader = ReferencesReader(r'./PDF_data','Liu_Invertible_Denoising_Network_A_Light_Solution_for_Real_Noise_Removal_CVPR_2021_paper.pdf')
reader.get_body()
print(reader.min_y,reader.max_y)
reader.find_references()
reader.split_references()