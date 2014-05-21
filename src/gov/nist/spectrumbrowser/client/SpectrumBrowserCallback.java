package gov.nist.spectrumbrowser.client;

public interface SpectrumBrowserCallback<T> {
	
	public void onSuccess(T result);
	
	public void onFailure(Throwable throwable);

}
