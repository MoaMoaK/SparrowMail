function addOptions (options, elt) {
	for (i=0 ; i<options.length ; i++) {
		var opt = document.createElement("option");
		opt.value = options[i];
		opt.innerHTML = options[i];
		elt.appendChild(opt);
	}
}

function dynDateElements(cbox) {
	if (cbox.checked) {
		var inputYear = document.createElement("select");
		inputYear.name = "endyear";
		var yearOpt = []; for (i=2017 ; i<2021 ; i++) { yearOpt.push(i.toString()); }
		addOptions(yearOpt, inputYear);

		var inputMonth = document.createElement("select");
		inputMonth.name = "endmonth";
		var monthOpt = []; for (i=1 ; i<13 ; i++) { monthOpt.push(i.toString()); }
		addOptions(monthOpt, inputMonth);
		
		var inputDay = document.createElement("select");
		inputDay.name = "endday";
		var dayOpt = []; for (i=1 ; i<31 ; i++) { dayOpt.push(i.toString()); }
		addOptions(dayOpt, inputDay);
		
		var inputHour = document.createElement("select");
		inputHour.name = "endhour";
		var hourOpt = []; for (i=0 ; i<25 ; i++) { hourOpt.push(i.toString()); }
		addOptions(hourOpt, inputHour);
		
		var inputMin = document.createElement("select");
		inputMin.name = "endmin";
		var minOpt = []; for (i=0 ; i<61 ; i++) { minOpt.push(i.toString()); }
		addOptions(minOpt, inputMin);
		                
		var inputSec = document.createElement("select");
		inputSec.name = "endsec";
		var secOpt = []; for (i=0 ; i<61 ; i++) { secOpt.push(i.toString()); }
		addOptions(secOpt, inputSec);

		var div = document.getElementById(cbox.name)
		div.insertAdjacentHTML('afterBegin', 'Set a time limit&nbsp;');
		div.appendChild(inputYear);
		div.appendChild(inputMonth);
		div.appendChild(inputDay);
		div.appendChild(inputHour);
		div.appendChild(inputMin);
		div.appendChild(inputSec);
	} else {
		var div = document.getElementById(cbox.name);
		while (div.hasChildNodes()) {
			div.removeChild(div.lastChild);
		}
	}
}

