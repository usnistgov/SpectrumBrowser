package gov.nist.spectrumbrowser.common;

public interface SpectrumBrowserCallback<T> {
	
	public void onSuccess(T result);
	
	public void onFailure(Throwable throwable);

}
