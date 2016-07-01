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


import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;

class FftPowerBand extends FrequencyBand{	
	public FftPowerBand(Sensor sensor) {
		super(sensor);
		this.threshold.put("samplingRate", new JSONNumber(-1));
		this.threshold.put("fftSize",new JSONNumber(-1));
	}
	
	public FftPowerBand(JSONObject threshold) {
		super(threshold);
	}

	public boolean validate() {
		if (!super.validate()  
				|| getSamplingRate() == -1 || getFftSize() == -1) {
			return false;
		} else {
			return true;
		}
	}
	
	public void setSamplingRate(long samplingRate) {
		if (samplingRate <= 0) {
			throw new IllegalArgumentException("Attempting to set an illegal value" + samplingRate);
		}
		threshold.put("samplingRate", new JSONNumber(samplingRate));
	}
	
	public long getSamplingRate() {
		if (threshold.get("samplingRate") != null) {
			return (long) threshold.get("samplingRate").isNumber().doubleValue();
		} else {
			return -1;
		}
	}

	public long getFftSize() {
		if (threshold.get("fftSize") != null) {
			return (long)threshold.get("fftSize").isNumber().doubleValue();
		} else {
			return -1;
		}
	}

	public void setFftSize(long fftSize) {
		if ( fftSize <= 0 ) {
			throw new IllegalArgumentException("Attempting to set an illegal value " + fftSize);
		} 
		threshold.put("fftSize", new JSONNumber(fftSize));
	}
	
}
