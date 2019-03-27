/*
Innen puskáztam az alapötletet: https://github.com/kubernetes/kubernetes/tree/master/test/images/resource-consumer

*/

var express = require('express');
var sleep = require('sleep');
var app = express();
var os = require('os');
var { exec } = require('child_process');
var d3 = require('d3-random');
//var winston = require('winston');
var moment = require('moment');
moment().utcOffset(2);

const fs = require('fs');

const path = '/media/server.log';
/*
winston.configure({
   format: winston.format.printf(info=>{
	return `${info.message}`;
   }), 
   transports:[
	new winston.transports.File({
		filename:path+'server.log',
	})
   ]
});
*/
/*
 /cpuStress/?duration=1000&cpuUsage=50&id=123&sleep=10	
duration: for how long do I want to take to serve the request
cpuUsage: how many percent of the cpu do I want to use (millicores) -> 200 ~ 20%
id: id of the request (see in logs)
sleep: sleep time if the cpu usage is high
*/
var podMillicores=500;
var format = 'HH:mm:ss:SSS,DD.MM.YYYY';
var secret = 'bacluster12345';
app.get('/', function(req,res,next){
   var token = req.query.token;
   if(token == secret ){
      next();
   }else{
      res.status(400).send('Bad request.');
   }
})

app.get('/cpuStress',function(req,res,next){
	var startTime = Date.now();
	var duration = req.query.duration;
	var cpuUsage = req.query.cpuUsage;
	var id = req.query.id;
	var sleepTime = req.query.sleep || 10;

	var requiredSleepTime = Math.round( (50*30)/(cpuUsage/10)) - 50;
	requiredSleepTime = requiredSleepTime  <= 0 ? 1:requiredSleepTime;
	duration  = duration - 50 - requiredSleepTime;
	duration =duration <= 0? 1:duration;
	checkCPU(startTime,duration,cpuUsage,res,sleepTime,requiredSleepTime);
	var endTime = Date.now();
	var log = id + ';' + moment(endTime+requiredSleepTime).format(format)+
		  ';'+moment(startTime).format(format);
	//winston.info(log);
	//exec('echo "'+log+'" >> '+path+'server.log',(err,stdout,stderr)=>{
	//   res.send('OK');
	//});
	//res.send('OK');
	fs.appendFileSync(path,log+'\n');
	sleep.msleep(requiredSleepTime);
	res.send('OK');
});

app.get('/exponential_serving',function(req,res,next){
        var startTime = Date.now();
        var id = req.query.id;
	var rate = req.query.rate
	var servingTimeGenerator = d3.randomExponential(rate);
	var servingTime = servingTimeGenerator()*1000;
	console.log(servingTime);
	while(Date.now()-startTime < servingTime){
		doTheMath(false,300)
	}
	
        var log = id + ';' + moment(Date.now()).format(format)+
                  ';'+moment(startTime).format(format);
        //winston.info(log);
        //exec('echo "'+log+'" >> '+path+'server.log',(err,stdout,stderr)=>{
        //   res.send('OK');
        //});
        //res.send('OK');
        fs.appendFileSync(path,log+'\n');
        res.send('OK');
});



function checkCPU(startTime, duration, cpuUsage,res,sleepTime){
	var cpu = process.cpuUsage();
	var hrtime = process.hrtime(); 
	sleep.msleep(5);
	doTheMath(true, cpuUsage);
	var avg=0;
	var count = 0;
	while(Date.now()-startTime < duration){
		count++;
		//count cpu usage here
		var cpu2 = process.cpuUsage(cpu);
		var hrtime2=process.hrtime(hrtime);
		var value = ((cpu2.system+cpu2.user)/1000.0)/(hrtime2[0]*1000.0 + hrtime2[1]/1000000.0)*100;
		//cpu millicores used
		//var value = (cpu2.user+ cpu2.system)/1000.0;
		//console.log(value);
		//-----------------------
		//if(value < cpuUsage){
		//console.log('---');
		//console.log(podMillicores*cpuUsage/100);
		if(value  < cpuUsage/10){
			doTheMath(false,cpuUsage);
			//console.log(avg/count);
			//console.log('---');
		}else{
			//console.log('sleep');
			sleep.msleep(sleepTime);
		}
	}
}

function doTheMath(boost=false, cpu = 100){
	//console.log('mateking');
	var count = cpu/30;
	if(boost){
		count = 30*cpu/10;
	}
	var res = 0;
	for(var i=0;i<count;i++){
	   for(var j=0;j<1000;j++){
		res+=Math.atan(i)*Math.tan(j);
	   }
	}
}

/*
I use the stress command 

 /memStress/?duration=1000&memUsage=50&id=1

duration: for how long do I want to use the memory
memUsage: how many percent of the memory do I want to use
id: id of the request (see in logs)
*/

var memSize = 256;

app.get('/memStress',function(req,res,next){
	var startTime = Date.now();
	var duration = req.query.duration;
	var memUsage = req.query.memUsage;
	var id = req.query.id;
	console.log(memUsage + ' ' + duration);
	exec('stress -m 1 --vm-bytes '+memUsage+'M --vm-hang 0 -t '+duration/1000+'s',(err, stdout, stderr)=>{
		console.log(stdout);
		if(err){
			res.status(500).send(err);
		} else {
			var endTime = Date.now();
        		var log = id + ';' + moment(endTime).format(format)+
                  		';'+moment(startTime).format(format);
        		winston.info(log);
			res.send('OK');
		}
	})
});

app.listen(8080, ()=>{
	console.log('server listen');
});

