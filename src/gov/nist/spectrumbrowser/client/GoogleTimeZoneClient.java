package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.http.client.Request;
import com.google.gwt.http.client.RequestBuilder;
import com.google.gwt.http.client.RequestCallback;
import com.google.gwt.http.client.RequestException;
import com.google.gwt.http.client.Response;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;

// This class is not used. TBD -- remove it.
public class GoogleTimeZoneClient {
	double latitude;
	double longitude;
	private String timeZoneName;
	private long time;
	private long localTime;
	private long utcOffset;
	private String timeZoneId;
	private long dstOffset;
	private long rawOffset;
	
	private static final Logger logger = Logger.getLogger("SpectrumBrowser");
	
	public GoogleTimeZoneClient( double latitude, double longitude, long time) {
		this.latitude = latitude;
		this.longitude = longitude;
		this.time = time;
		
	}
	
	void dispatch(final Runnable runnable) {
		// Continue here.
		// Get the local time for the max date in the range.
		String url = "https://maps.googleapis.com/maps/api/timezone/json?location="
				+ latitude
				+ ","
				+ longitude
				+ "&timestamp="
				+ time
				+ "&sensor=true&key=" + SpectrumBrowser.API_KEY;
		
		RequestBuilder requestBuilder = new RequestBuilder(RequestBuilder.POST, url);
		requestBuilder.setCallback(new RequestCallback() {
			@Override
			public void onResponseReceived(Request request,
					Response response) {
				try {
					String text = response.getText();
					logger.finer("GoogleTimeZoneClient: JSON String " + text);
					JSONObject jsonObj = (JSONObject) JSONParser
							.parseLenient(text);
					
					dstOffset = (long) jsonObj.get("dstOffset")
							.isNumber().doubleValue();
					rawOffset = (long) jsonObj.get("rawOffset")
							.isNumber().doubleValue();
					utcOffset = dstOffset + rawOffset;
					localTime =   time + utcOffset;
					
					logger.finest("Google time server computed " + time + " localTime " + localTime + " dstOffset " + " rawOffset " + rawOffset);
					
					timeZoneId = jsonObj.get("timeZoneId").isString()
							.stringValue();
					timeZoneName = jsonObj.get("timeZoneName")
							.isString().stringValue();
					runnable.run();

				} catch (Exception ex) {
					logger.log(Level.SEVERE, "Error processing  timeZone response",
							ex);
				}
			}
			@Override
			public void onError(Request request, Throwable exception) {
				logger.log(Level.SEVERE, "Error getting timeZone",
						exception);

			}
		}				
		);
			
		try {
			requestBuilder.send();
		} catch (RequestException exception) {			
			logger.log(Level.SEVERE, "Error getting timeZone",
					exception);
		}		
	}

	public String getTimeZoneName() {
		return timeZoneName;
	}

	

	public String getTimeZoneId() {
		return timeZoneId;
	}
	
	public int getOffsetInMinutes() {
		return (int) (rawOffset/60);
	}

	public long getLocalTime() {
		return localTime;
	}

	
	public long getUtcOffset() {
		return this.utcOffset;
	}

	

}
