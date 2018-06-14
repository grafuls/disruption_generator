## In case of manual execution

(files_to_watch,regex,command_to_exec,ip,username,password,
ip_for_execute_command,remote_username,remote_password,time_out)

1. in case of remote machine:
	- ip: the remote machine IP
	- username/password: authentication

2. for all cases (local & remote)
	- files_to_watch: absolute path of the file that should be watched (
	  start with "/")
	- regex: regular expression to look for
	- command_to_exec: the command that should be executed in case that
	  the regex has found. If not needed, pass None
	- ip_for_execute_command: the !!! IP !!! of the machine that the
	  command should exec on
	- remote_username: username for the second machine
	- remote_password: password for the second machine
	- time_out: limited time for watching

## Options

	* -m, --machine : if the file is on remote machine then '-m' followed

	  by ip,username & password

	  (e.g. -m 10.0.0.0 root P@SSW0RD)

	* -f,--files : option that followed by the absolute path of the files

	  that need to watch for.

	  each file should be preceded by -f separately

	  (e.g. -f /var/log/vdsm/vdsm.log -f /tmp/my_log)

	* -r, --regex : option for regex (e.g. -r <REGULAR_EXPRESSION>)

	* -c, --command : followed by the command that should be executed in

	  case of log event

	  (e.g. -c 'ls -l') <- note that parameters with white space MUST be

	  surrounds by " ' "

	* -M, --Machine : in case that the command should executes on

	  different machine , this option followed

	  by IP,username & password

	  (e.g. -M 10.0.0.0 root P@SSW0RD)

	* -t, --timeout : limited time for watching

	  (e.g. -t 3)
