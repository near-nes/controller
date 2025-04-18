import os
import mpi4py

def collapse_files(dir, names, pops, njt):
    files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir,f))]
    pops_dict = {name: pop for name, pop in zip(names, pops)}

    if mpi4py.MPI.COMM_WORLD.rank == 0:
        for name, pop in pops_dict.items():
            file_list = [] 
            senders = []
            times = []
            
            for f in files:
                if f.startswith(name):
                    file_list.append(f)
            
            combined_data = []
            
            for f in file_list:
                with open(dir + f, "r") as fd:
                    lines = fd.readlines()
                    for line in lines:
                        if line.startswith("#") or line.startswith("sender"):
                            continue 
                        combined_data.append(line.strip()) 
            
            unique_lines = list(set(combined_data))
            
            for line in unique_lines:
                sender, time = line.split()
                senders.append(int(sender))
                times.append(float(time))

            for i in range(njt):
                pop[i].gather_data(senders, times)

            with open(dir + name + ".gdf", "a") as wfd:
                for line in unique_lines:
                    wfd.write(line + "\n") 
            for f in file_list:
                os.remove(dir + f)

        print('Collapsing files ended')

def collapse_files_bullet(dir, names, njt):
    files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir,f))]
    print("sto entrando")
    print("sono entrato")
    for name in names:
        file_list = [] 
        senders = []
        times = []
            
        for f in files:
            if f.startswith(name):
                file_list.append(f)
        print(file_list)
        combined_data = []
            
        for f in file_list:
            with open(dir + f, "r") as fd:
                lines = fd.readlines()
                print(lines)
                for line in lines:
                    if line.startswith("#") or line.startswith("sender"):
                        continue 
                    combined_data.append(line.strip()) 
            
        unique_lines = list(set(combined_data))
            
        for line in unique_lines:
            sender, time = line.split()
            senders.append(int(sender))
            times.append(float(time))
            '''
            for i in range(njt):
                pop[i].gather_data(senders, times)
            '''
        with open(dir + "unified/" + name + ".gdf", "w") as wfd:
            for line in unique_lines:
                wfd.write(line + "\n") 
        #for f in file_list:
            #os.remove(dir + f)
    print('Collapsing files ended (Bullet)')

def add_entry(exp):
    path = exp.pathData
    init_pos_ee = exp.init_pos 
    tgt_pos_ee = exp.tgt_pos

    dynSys = exp.dynSys
    init_pos = dynSys.inverseKin( init_pos_ee )
    tgt_pos  = dynSys.inverseKin( tgt_pos_ee )

    search_path = os.path.join(path, "nest/")
    files = [f for f in os.listdir(search_path) if f.startswith("out") and os.path.isfile(os.path.join(search_path, f))]
    
    for file in files:
        senders = []
        times = []
        with open(search_path + file, "r") as fd:
                    lines = fd.readlines()
                    #print(lines)
                    for line in lines:
                        sender, time = line.split()
                        senders.append(int(sender))
                        times.append(float(time))
        if file.startswith("out_p"):
            senders_p = senders
            times_p = times
        else:
            senders_n = senders
            times_n = times    

    with open(path + "dataset_spikes" + ".gdf", "a") as wfd:
        wfd.write(f"{init_pos_ee} {tgt_pos_ee} ")
        senders_p_str = '[' + ' '.join(map(str, senders_p)) + ']'
        times_p_str = '[' + ' '.join(map(str, times_p)) + ']'

        senders_n_str = '[' + ' '.join(map(str, senders_n)) + ']'
        times_n_str = '[' + ' '.join(map(str, times_n)) + ']'
    
        wfd.write(f"{senders_p_str} {times_p_str} {senders_n_str} {times_n_str}\n")
    
    print("Trajectory added to dataset.")