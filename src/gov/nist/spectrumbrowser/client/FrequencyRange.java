package gov.nist.spectrumbrowser.client;

class FrequencyRange {
	long minFreq;
	long maxFreq;
	String sys2detect;

	public FrequencyRange(String sys2detect, long minFreq, long maxFreq) {
		this.minFreq = minFreq;
		this.maxFreq = maxFreq;
		this.sys2detect = sys2detect;
	}

	@Override
	public boolean equals(Object that) {
		FrequencyRange thatRange = (FrequencyRange) that;
		return this.minFreq == thatRange.minFreq
				&& this.sys2detect.equals(thatRange.sys2detect)
				&& this.maxFreq == thatRange.maxFreq;
	}

	@Override
	public int hashCode() {
		return (Long.toString(maxFreq + minFreq) + sys2detect).hashCode();
	}

	@Override
	public String toString() {
		return sys2detect + " "
				+ Double.toString((double) minFreq / 1000000.0) + " MHz - "
				+ Double.toString((double) (maxFreq / 1000000.0)) + " MHz";
	}
}