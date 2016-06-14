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
