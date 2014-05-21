package gov.nist.spectrumbrowser.client;


import java.util.logging.Handler;
import java.util.logging.LogRecord;

public class SpectrumBrowserLoggingHandler extends Handler {

	SpectrumBrowserServiceAsync spectrumBrowserService;

	public SpectrumBrowserLoggingHandler(SpectrumBrowserServiceAsync spectrumBrowserService) {
		this.spectrumBrowserService = spectrumBrowserService;
	}

	@Override
	public void publish(LogRecord record) {
		String messageToLog;
		String message = record.getMessage();
		messageToLog =  message + "\n";
		Throwable thrown = record.getThrown();
		while (thrown != null) {
			messageToLog += thrown.getMessage();
			messageToLog += "StackTrace : \n";
			StackTraceElement[] stackTrace = thrown.getStackTrace();
			for (int i = 0; i < stackTrace.length; i++) {
				String ste = stackTrace[i].getMethodName() + ":"
						+ stackTrace[i].getLineNumber() + "\n";
				messageToLog += ste;
			}
			if (thrown.getCause() != null) {
				messageToLog += "Caused By :";
			}
			thrown = thrown.getCause();
		}
		spectrumBrowserService.log(messageToLog);
	}

	@Override
	public void flush() {
		
	}

	@Override
	public void close() {
		
	}

}
