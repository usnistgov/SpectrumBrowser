/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.admin;


import com.google.gwt.json.client.JSONObject;

class SweptFrequencyBand extends FrequencyBand {
	
	public SweptFrequencyBand(Sensor sensor) {
		super(sensor);
	}
	
	public SweptFrequencyBand(JSONObject threshold) {
		super(threshold);
	}

	public boolean validate() {
		if (getSystemToDetect().equals("UNKNOWN") || 
				getMaxFreqHz() == -1 || getMinFreqHz() == -1 || getThresholdDbmPerHz() == -1  ||
				getMinFreqHz() > getMaxFreqHz() || getChannelCount() == -1 ) {
			return false;
		} else {
			return true;
		}
	}
	
}