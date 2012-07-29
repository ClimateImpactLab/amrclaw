#!/usr/bin/env python

r"""
Parse log files generated by run_thread_tests.py

Command line options:
    -v, --verbose - Verbose output (default == False)
    -p, --path=(string) - Path to directory containing log files 
                          (default == LOG_FILE_BASE in run_thread_tests.py)
    -f, --format=(string) - Format of plot output, can be anything that
                            matplotlib can understand (default == 'pdf')
    -F, --force - Force time file parsing
    -a, --amr - Plot compound AMR based plots (default is False)
    --tick, --notick - Plot tick based timings (default is False)
    --time, --notime - Plot time based timings (default is True)
    --effec - Plot efficiency plots (default is False)
    -h, --help - Display help message
"""

import sys
import os
import re
import glob
import math
import getopt
    
import matplotlib.pyplot as plt

import run_thread_tests

log_regex = re.compile(r"\*{3}\sOMP_NUM_THREADS\s=\s.*|\*{7}\stick\stiming\s=\s+.*\ss{1}")
time_regex = re.compile(r"\*{3}\sOMP_NUM_THREADS\s=\s.*|\s+Elapsed\s\(wall\sclock\).*") # \s+User\stime\s\(seconds\)\:\s.*

class ParsingError(Exception):
    
    def __init__(self,path,threads,times):
        self.path = path
        self.threads = threads
        self.times = times
        
        msg =  "Parsing may not have been successful, len(threads) != len(times)."
        msg += "\n\tpath = %s" % path
        msg += "\n\tthreads = %s" % threads
        msg += "\n\ttimes = %s" % times
        self.msg = msg
        
    def __str__(self):
        return self.msg
        
        

def expand_path(path):
    return os.path.expandvars(os.path.expanduser(path))

def parse_log_file(path,verbose=True):
    # Open contents of log file 
    log_contents = open(path,'r').read()
    
    # Loop through regular expression finds
    threads = []
    times = []
    for match in log_regex.finditer(log_contents):
        if "OMP_NUM_THREADS" in match.group():
            threads.append(int(match.group().strip("*** OMP_NUM_THREADS =")))
            if verbose:
                print "Threads = %s" % threads[-1]
        elif "tick timing" in match.group():
            times.append(float(match.group().strip("******* tick timing =")[:-1]))
            if verbose:
                print "Time = %s" % times[-1]
    
    if not len(threads) == len(times):
        raise ParsingError(path,threads,times)
    
    return threads,times

def parse_time_file(path,verbose=True):
    # Open contents of log file
    log_contents = open(path,'r').read()
    
    # Loop through regular expression finds
    threads = []
    times = []
    for match in time_regex.finditer(log_contents):
        if "OMP_NUM_THREADS" in match.group():
            threads.append(int(match.group().strip("*** OMP_NUM_THREADS =")))
            if verbose:
                print "Threads = %s" % threads[-1]
        # This parsing assumes that we never roll over to hours
        elif "Elapsed (wall clock) time" in match.group():
            raw_time = match.group().strip().strip("Elapsed (wall clock) time (h:mm:ss or m:ss): ")
            [minutes,seconds] = raw_time.split(':')
            times.append(float(minutes)*60+float(seconds))
            if verbose:
                print "Time = %s" % times[-1]
    
    if not len(threads) == len(times):
        raise ParsingError(path,threads,times)
    
    return threads,times

def create_timing_plots(log_paths,plot_path='./plots',out_format='png',
                                  out_file_base='plot',figsize=(8,6)
                                  ,verbose=False):
    
    # Create the directory for the plots if it does not already exist
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    if not os.path.isdir(plot_path):
        print >> sys.stderr, "File already exists with the same name as the "
        print >> sys.stderr, "requested plot directory %s." % plot_path
        sys.exit(42)
    
    # Go through each log file and parse it
    for (i,path) in enumerate(log_paths):
        try:
            # Parse the log file
            if verbose:
                print os.path.basename(path)[:-4]
            if os.path.basename(path)[0:3] == "log":
                log_name = os.path.basename(path).strip('log_')[:-4]
                threads,times = parse_log_file(path,verbose=verbose)
            elif os.path.basename(path)[0:4] == "time":
                log_name = os.path.basename(path).strip('time_')[:-3]
                threads,times = parse_time_file(path,verbose=verbose)
            if verbose:
                print threads,times

            # Plot this run
            fig = plt.figure(figsize=figsize)
            axes = fig.add_subplot(111)
            axes.plot(threads,times,'or-')
        
            # Labeling
            axes.set_xbound(threads[0]-0.5,threads[-1]+0.5)
            axes.set_title(log_name)
            axes.set_xlabel('Number of Threads')
            axes.set_xticks(threads)
            axes.set_xticklabels(threads)
            axes.set_ylabel('Time (s)')

            # Matplotlib version > 1.0 only support tight_layout
            try:
                plt.tight_layout()
            except:
                pass

            if out_format is not None:
                file_name = '%s_%s.%s' % (log_name,out_file_base,out_format)
                if verbose:
                    print file_name
                    print "Saving plot to %s" % os.path.join(plot_path,file_name)
                plt.savefig(os.path.join(plot_path,file_name))
            else:
                plt.show()

        except ParsingError as e:
            print >> sys.stderr, e
            print >> sys.stderr, "\tcontinuing..."
            
                
def create_efficiency_plots(log_paths,plot_path='./plots',
                                  out_format='png',
                                  out_file_base='plot',figsize=(8,6),
                                  colors=['blue','green','red','purple','gray','turquoise','magenta','yellow'],
                                  verbose=False):
    r"""Create compound plots with multiple efficiencies compared in one plot"""
    
    # Create the directory for the plots if it does not already exist
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    if not os.path.isdir(plot_path):
        print >> sys.stderr, "File already exists with the same name as the "
        print >> sys.stderr, "requested plot directory %s." % plot_path
        sys.exit(42)
    
    efficiencies = []
    names = []
    
    # Go through each log file and parse it
    for (i,path) in enumerate(log_paths):
        try:
            # Parse the log file
            if verbose:
                print os.path.basename(path)[:-4]
            if os.path.basename(path)[0:3] == "log":
                log_name = os.path.basename(path).strip('log_')[:-4]
                threads,times = parse_log_file(path,verbose=verbose)
            elif os.path.basename(path)[0:4] == "time":
                log_name = os.path.basename(path).strip('time_')[:-3]
                threads,times = parse_time_file(path,verbose=verbose)
            if verbose:
                print threads,times

            # Calculate efficiency, p=1 is basis
            names.append(log_name)
            efficiencies.append([times[0] * threads[0] / (time * threads[i]) for (i,time) in enumerate(times)])
        except ParsingError as e:
            print >> sys.stderr, e
            print >> sys.stderr, "\tcontinuing..."


    # Plot this run
    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    for i in xrange(len(efficiencies)):
        axes.plot(threads,efficiencies[i],'o-',color=colors[i],label=names[i])    
    axes.plot(threads,[1 for thread in threads],'k--')
        
    # Labeling
    axes.set_xbound(threads[0]-0.5,threads[-1]+0.5)
    axes.set_ybound(0.0,1.1)
    # axes.set_title(log_name)
    axes.set_xlabel('Number of Threads')
    axes.set_xticks(threads)
    axes.set_xticklabels(threads)
    axes.set_ylabel('Efficiency')
    axes.legend(loc=1)

    # Matplotlib version > 1.0 only support tight_layout
    try:
        plt.tight_layout()
    except:
        pass

    if out_format is not None:
        file_name = '%s_%s.%s' % (log_name,out_file_base,out_format)
        if verbose:
            print file_name
            print "Saving plot to %s" % os.path.join(plot_path,file_name)
        plt.savefig(os.path.join(plot_path,file_name))
    else:
        plt.show()
    
 
def create_amr_plots(log_paths,threading_type,plot_path='./plots',
                                  out_format='png',
                                  out_file_base='plot',figsize=(8,6),
                                  colors=['blue','green','red','black','purple','gray','turquoise','magenta'],
                                  verbose=False):
    r"""Create compound plots with multiple timings on one plot."""
    
    # Create the directory for the plots if it does not already exist
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    if not os.path.isdir(plot_path):
        print >> sys.stderr, "File already exists with the same name as the "
        print >> sys.stderr, "requested plot directory %s." % plot_path
        sys.exit(42)
        
    # Storage
    threads = []
    times = []
    max1d = []
        
    # Go through each log file and parse it
    for (i,path) in enumerate(log_paths):
        try:
            # Parse the log file
            if os.path.basename(path)[0:3] == "log":
                log_name = os.path.basename(path).strip('log_')[:-4]
                max1d.append(log_name[14:-3])
                new_threads,new_times = parse_log_file(path,verbose=verbose)
            elif os.path.basename(path)[0:4] == "time":
                log_name = os.path.basename(path).strip('time_')[:-3]
                max1d.append(log_name[14:-3])
                new_threads,new_times = parse_time_file(path,verbose=verbose)
            if verbose:
                print "Parsing log file = %s" % log_name
                print new_threads,new_times
            
            threads.append(new_threads)
            times.append(new_times)    
        except ParsingError as e:
            print >> sys.stderr, e
            print >> sys.stderr, "\tcontinuing..."
        
    # Plot these runs
    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    min_threads = 10**10
    max_threads = 0
    for i in xrange(0,len(threads)):
        axes.plot(threads[i],times[i],'o-',color=colors[i],label='max1d=%s' % max1d[i])
        min_threads = min(min_threads,threads[i][0])
        max_threads = max(max_threads,threads[i][-1])
        
    # Labeling
    axes.set_xbound(min_threads-0.5,max_threads+0.5)
    axes.set_title(threading_type)
    axes.set_xlabel('Number of Threads')
    axes.set_xticks(threads[-1])
    axes.set_xticklabels(threads[-1])
    axes.set_ylabel('Time (s)')
    axes.legend(loc=1)

    # Matplotlib version > 1.0 only support tight_layout
    try:
        plt.tight_layout()
    except:
        pass

    if out_format is not None:
        file_name = '%s_%s.%s' % (threading_type,out_file_base,out_format)
        if verbose:
            print file_name
            print "Saving plot to %s" % os.path.join(plot_path,file_name)
        plt.savefig(os.path.join(plot_path,file_name))
    else:
        plt.show()
    

help_message = __doc__

class Usage(Exception):
    def __init__(self,msg):
        self.msg = msg   

if __name__ == "__main__":
    # Parse command line arguments
    try:
        try:
            opts,args = getopt.getopt(sys.argv[1:],
                            "hvp:f:a",
                            ['help','verbose','path=','tick','notick',
                             'notime','time','format=','effec','amr'])
                                
        except getopt.error, msg:
            raise Usage(msg)
        
        # Default values
        verbose = False
        log_dir = './logs_%s' % os.environ["FC"]
        format = 'png'
        force = False
        tick_plots = True
        time_plots = False
        efficiency_plots = False
        amr_plots = False
    
        # Option parsing
        for option,value in opts:
            if option in ("-v","--verbose"):
                verbose = True
            if option in ("-p",'--path'):
                log_dir = value
            if option in ('-f','--format'):
                format = value
            if option in ('--notime'):
                time_plots = False
            if option in ('--time'):
                time_plots = True
            if option in ('--notick'):
                tick_plots = False
            if option in ('--tick'):
                tick_plots = True
            if option in ('--effec'):
                efficiency_plots = True
            if option in ('-a','--amr'):
                amr_plots = True
            if option in ("-h","--help"):
                raise Usage(help_message)
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        # print >> sys.stderr, "\t for help use --help"
        sys.exit(2)

    if tick_plots:
        # Find log files
        log_files = glob.glob(expand_path(os.path.join(log_dir,"log*.txt")))
        if verbose:
            print "Found these log files:"
            print '\t\n'.join(log_files)
        if len(log_files) == 0:
            print >> sys.stderr, "Did not find any log files at:"
            print >> sys.stderr, "\t%s" % log_dir
            sys.exit(2)
        
        # Find and parse all log files found in log_dir
        create_timing_plots(log_files,plot_path='./plots/tick',out_format=format,out_file_base='tick_plot',verbose=verbose)

    if time_plots and not os.uname()[0] == 'Darwin':
        # Only use the timing files if we are not on Darwin (time does not work as awesome there)
        time_files = glob.glob(expand_path(os.path.join(log_dir,"time*.txt")))
        if verbose:
            print "Found these time files:"
            print '\t\n'.join(log_files)
        if len(log_files) == 0:
            print >> sys.stderr, "Did not find any time files at:"
            print >> sys.stderr, "\t%s" % log_dir
            sys.exit(2)
        create_timing_plots(time_files,plot_path='./plots/time',
                            out_format=format,out_file_base='time_plot',
                            verbose=verbose)
                            
    # Efficiency plots
    if efficiency_plots:
        for test_type in ['amr_grid','amr_sweep','single_sweep','static_grid','weak_sweep']:
            log_files = glob.glob(expand_path(os.path.join(log_dir,"log_%s*.txt" % test_type)))
            if verbose:
                print "Found these log files:"
                print '\t\n'.join(log_files)
            if len(log_files) == 0:
                print >> sys.stderr, "Did not find any log files at:"
                print >> sys.stderr, "\t%s" % log_dir
                exit
            create_efficiency_plots(log_files,plot_path="./plots/effec",
                                    out_format=format,out_file_base='%s_effec_plot' % test_type,
                                    verbose=verbose)
        
    # Make compound amr plots
    if amr_plots:
        log_files = glob.glob(expand_path(os.path.join(log_dir,"log_amr_sweep*.txt")))
        if verbose:
            print "Found these amr log files:"
            print '\t\n'.join(log_files)
        if len(log_files) == 0:
            print >> sys.stderr, "Did not find any amr log files at:"
            print >> sys.stderr, "\t%s" % log_dir
            # sys.exit(2)
        
        create_amr_plots(log_files,'sweep',plot_path='./plots/amr',
                         out_format=format,out_file_base="amr_plot",
                         verbose=verbose)
        
        log_files = glob.glob(expand_path(os.path.join(log_dir,"log_amr_grid*.txt")))
        if verbose:
            print "Found these amr log files:"
            print '\t\n'.join(log_files)
        if len(log_files) == 0:
            print >> sys.stderr, "Did not find any amr log files at:"
            print >> sys.stderr, "\t%s" % log_dir
            # sys.exit(2)
        
        create_amr_plots(log_files,'grid',plot_path='./plots/amr',
                  out_format=format,out_file_base="amr_plot",
                  verbose=verbose)    
                         
        

        
