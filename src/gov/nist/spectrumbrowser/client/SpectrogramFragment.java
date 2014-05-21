package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.client.Spectrogram.SpectrogramDragHandler;

import java.util.ArrayList;
import java.util.Date;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.canvas.client.Canvas;
import com.google.gwt.canvas.dom.client.Context2d;
import com.google.gwt.canvas.dom.client.CssColor;
import com.google.gwt.dom.client.ImageElement;
import com.google.gwt.event.dom.client.DoubleClickEvent;
import com.google.gwt.event.dom.client.DoubleClickHandler;
import com.google.gwt.event.dom.client.ErrorEvent;
import com.google.gwt.event.dom.client.ErrorHandler;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.event.dom.client.MouseDownEvent;
import com.google.gwt.event.dom.client.MouseDownHandler;
import com.google.gwt.event.dom.client.MouseMoveEvent;
import com.google.gwt.event.dom.client.MouseMoveHandler;
import com.google.gwt.event.dom.client.MouseUpEvent;
import com.google.gwt.event.dom.client.MouseUpHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.reveregroup.gwt.imagepreloader.ImageLoadEvent;
import com.reveregroup.gwt.imagepreloader.ImageLoadHandler;
import com.reveregroup.gwt.imagepreloader.ImagePreloader;

public class SpectrogramFragment extends Composite {

	public static final long MILISECONDS_PER_DAY = 24 * 60 * 60 * 1000;

	static Logger logger = Logger.getLogger("SpectrumData");
	public long currentTime;
	public long currentFreq;
	private VerticalPanel spectrumAndOccupancyPanel;

	int minPower;
	int maxPower;
	int occupancyMinPower;
	Label currentValue = new Label(
			"Click on spectrogram for Spectrum and Occupancy");
	HorizontalPanel hpanel; // = new HorizontalPanel();
	VerticalPanel vpanel;// = new VerticalPanel();
	long minTime;
	long maxTime;
	long minFreq;
	long maxFreq;
	private double yPixelsPerMegahertz;
	private int canvasPixelWidth;
	private int canvasPixelHeight;
	private SpectrumLocationSelection spectrumLocationSelection;
	private Label maxPowerLabel;
	private Label minPowerLabel;
	private SpectrumBrowser spectrumBrowser;
	private String sessionId;
	private StatisticsChart spectrumChart;
	private StatisticsChart occupancyChart;
	private VerticalPanel spectrogramPanel;
	private VerticalPanel freqPanel;
	private HorizontalPanel powerMapPanel;
	private Canvas surface;
	private ArrayList<Region> regions = new ArrayList<Region>();
	private HorizontalPanel xaxisPanel;
	private VerticalPanel verticalOccupancySelector;
	private FitImage powerMapImage;
	private long mouseDownTime;
	private int clickCounter;
	private int mouseDownPosition;
	private SpectrogramDragHandler spectrogramDragHandler;
	private Image image;
	private Timer timer = null;

	private Spectrogram spectrogram;

	private VerticalPanel rootVerticalPanel;

	private String cmapUrl;

	class Region {
		long tmin;
		long tmax;

		Region(long tmin, long tmax) {
			this.tmin = tmin;
			this.tmax = tmax;

		}
	}

	/**
	 * Update the time and frequency readings on top of the plot if the user
	 * moves the mouse around in the canvas area.
	 * 
	 */
	public class SurfaceMouseMoveHandlerImpl implements MouseMoveHandler {

		@Override
		public void onMouseMove(MouseMoveEvent event) {
			int timeCoord = event.getRelativeX(event.getRelativeElement());
			int freqCoord = event.getRelativeY(event.getRelativeElement());
			double xratio = ((double) timeCoord / (double) canvasPixelWidth);
			double yratio = 1.0 - ((double) freqCoord / (double) canvasPixelHeight);

			currentFreq = (long) ((SpectrogramFragment.this.maxFreq - SpectrogramFragment.this.minFreq) * yratio)
					+ SpectrogramFragment.this.minFreq;
			currentTime = (long) ((SpectrogramFragment.this.maxTime - SpectrogramFragment.this.minTime) * xratio)
					+ SpectrogramFragment.this.minTime;
			currentValue.setText("Time = "
					+ spectrumLocationSelection
							.formatDateLong(currentTime) + "; Freq = "
					+ currentFreq + " MHz");
		}

	}

	

	/**
	 * This implements the spectrogram and power vs. time charts. Gets invoked
	 * when a user clicks on an location.
	 * 
	 */

	private void drawOccupancyAndSpectrum() {
		currentValue.setText("Generating plots. Please wait. ");
		logger.finer("currentTime = " + currentTime);
		spectrumBrowser.getSpectrumBrowserService().getPowerVsTimeAndSpectrum(
				sessionId, spectrumLocationSelection.getLocation(),
				currentTime, currentFreq, minTime, maxTime, minFreq, maxFreq,
				new SpectrumBrowserCallback<String>() {
					@Override
					public void onFailure(Throwable arg0) {
						spectrumBrowser.displayError("Error contacting server");
						return;
					}

					@Override
					public void onSuccess(String jsonString) {
						try {
							JSONValue jsonValue = JSONParser
									.parseStrict(jsonString);
							JSONObject jsonObject = jsonValue.isObject();
							if (!jsonObject.containsKey("spectrum")) {
								currentValue
										.setText("Spectrum Undefined -- cant generate plot");
								return;
							}
							if (!jsonObject.containsKey("PowerVsTime")) {
								currentValue
										.setText("PowerVsTime Undefined -- cant generate plot");
								return;
							}
							String spectrumImage = jsonObject.get("spectrum")
									.isString().stringValue();
							String occupancyImage = jsonObject
									.get("PowerVsTime").isString()
									.stringValue();
							logger.finer("PowerVsTime = " + occupancyImage + " Spectrum " + spectrumImage);
							if (spectrumImage != null && occupancyImage != null) {

								if (spectrumChart != null) {
									spectrumAndOccupancyPanel
											.remove(spectrumChart);

								}

								// Draw the spectrum chart.
								String url = spectrumBrowser.getBaseUrl()
										+ "getspectrogram?image="
										+ spectrumImage;
								spectrumChart = new StatisticsChart(
										url, canvasPixelWidth,
										canvasPixelHeight);
								
								spectrumChart.draw();
								// add it to the screen.
								spectrumAndOccupancyPanel.add(spectrumChart);
								spectrumChart.setVisible(true);
								// do the same for the power vs. time chart
								if (occupancyChart != null) {
									spectrumAndOccupancyPanel
											.remove(occupancyChart);
								}
								String cmapUrl = spectrumBrowser.getBaseUrl()
										+ "getspectrogram?image="
										+ occupancyImage;
								occupancyChart = new StatisticsChart(
										cmapUrl, canvasPixelWidth,
										canvasPixelHeight);
								occupancyChart.draw();
								spectrumAndOccupancyPanel.add(occupancyChart);

								occupancyChart.setVisible(true);
								currentValue.setText("Scroll down to see the generated plots");
							}
						} catch (Exception ex) {
							logger.log(Level.SEVERE, "Exception occured ", ex);
						}

					}
				});

	}

	public void setMinMaxPower(int minPower, int maxPower, int occupancyMinPower) {
		if (maxPower == minPower) {
			logger.log(Level.SEVERE, "maxPower " + maxPower + " minPower "
					+ minPower);
		}
		this.minPower = minPower;
		this.maxPower = maxPower;

		this.minPowerLabel.setText(minPower + " dBm");
		this.maxPowerLabel.setText(maxPower + " dBm");
		this.occupancyMinPower = occupancyMinPower;
	}

	public double getXFromTime(long time) {
		return (double) ((time - minTime) * this.getxPixelsPerMilisecond());
	}

	public double getYFromFreq(long freq) {
		return (double) canvasPixelHeight - (double) canvasPixelHeight
				* (double) (freq - minFreq) / (double) (maxFreq - minFreq);
	}

	

	/**
	 * Add a dead region to the graph
	 * 
	 * @param tmin
	 * @param tmax
	 * @param fmin
	 * @param fmax
	 */
	public void addDeadRegion(long tmin, long tmax) {
		logger.log(Level.FINE, "SpectrogramFragment.addDeadRegion(): tmin = "
				+ tmin + " tmax= " + tmax);
		Region region = new Region(tmin, tmax);
		this.regions.add(region);
	}

	/**
	 * Plots a spectrogram on a canvas.
	 * 
	 * @param spectrogramDragHandler
	 * 
	 * @param powerDataDbm
	 *            -- the power values in dbm.
	 * @param time
	 *            -- the time array in miliseconds standard time (UTC after Jan1
	 *            1970).
	 * @param frequencies
	 *            -- the frequency Array in MHz.
	 * @param currentValue
	 *            -- the label to update when the user clicks on the canvas.
	 * @param scale
	 *            -- the scale for the plot in pixels per reading.
	 */
	public SpectrogramFragment(long minTime, long maxTime, long minFreq,
			long maxFreq, int canvasXmax, int canvasYmax, String sessionId,
			SpectrumLocationSelection spectrumLocationSelection,
			SpectrumBrowser spectrumBrowser, VerticalPanel rootVerticalPanel,
			Spectrogram spectrogram,
			SpectrogramDragHandler spectrogramDragHandler) {
		this.minTime = minTime;
		this.maxTime = maxTime;
		this.minFreq = minFreq;
		this.maxFreq = maxFreq;
		this.canvasPixelWidth = canvasXmax;
		this.canvasPixelHeight = canvasYmax;
		this.spectrumLocationSelection = spectrumLocationSelection;
		this.spectrumBrowser = spectrumBrowser;
		this.sessionId = sessionId;
		this.spectrogramDragHandler = spectrogramDragHandler;
		this.spectrogram = spectrogram;
		this.rootVerticalPanel = rootVerticalPanel;
		vpanel = new VerticalPanel();
		initWidget(vpanel);

		logger.log(Level.FINE, "SpectrogramFragment: minTime: " + minTime
				+ " maxTime: " + maxTime + " minFreq " + minFreq + " maxFreq "
				+ maxFreq + " canvasXmax " + canvasXmax + " canvasYmax ");
	}

	public void draw() {

		try {
			vpanel.clear();
			hpanel = new HorizontalPanel();

			hpanel.setSpacing(10);

			this.setStyleName("spectrumData");
			String minColor = this.getStyleElement().getPropertyString(
					"min-color");
		
			
			// Calculate scales.
			

			// Create the main drawing surface.
			logger.log(Level.FINER, "canvasXmax " + canvasPixelWidth
					+ " xPixelsPerMilisecond " + getxPixelsPerMilisecond());

			// TODO -- define it in css
			String startDate = spectrumLocationSelection.formatDate(minTime);
			String endDate = spectrumLocationSelection.formatDate(maxTime);
			xaxisPanel = new HorizontalPanel();
			xaxisPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			HorizontalPanel xaxis = new HorizontalPanel();
			xaxis.setWidth(canvasPixelWidth + 30 + "px");
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);

			xaxis.add(new Label(startDate));
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			xaxis.add(new Label("Date"));
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
			xaxis.add(new Label(endDate));
			xaxisPanel.add(xaxis);

			// Attach the labels for the spectrogram power
			VerticalPanel powerLevelPanel = new VerticalPanel();
			powerLevelPanel.setWidth(100 + "px");
			this.maxPowerLabel = new Label();
			this.minPowerLabel = new Label();
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			powerLevelPanel.add(maxPowerLabel);
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
			powerLevelPanel.add(new Label("Power (dBm) "));
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
			powerLevelPanel.add(minPowerLabel);

			// Attach labels for the frequency.
			freqPanel = new VerticalPanel();
			freqPanel.setWidth(100 + "px");
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			freqPanel.add(new Label(Long.toString(maxFreq)));
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
			freqPanel.add(new Label("Frequency (MHz)"));
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
			freqPanel.add(new Label(Long.toString(minFreq)));

			powerMapPanel = new HorizontalPanel();
			powerMapPanel.setWidth(30 + "px");
			hpanel.add(freqPanel);
			spectrogramPanel = new VerticalPanel();

			HorizontalPanel spectrogramAndPowerMapPanel = new HorizontalPanel();
			spectrogramAndPowerMapPanel.add(spectrogramPanel);
			spectrogramAndPowerMapPanel.add(powerMapPanel);
			hpanel.add(spectrogramAndPowerMapPanel);

			vpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			vpanel.add(this.currentValue);
			vpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			vpanel.add(hpanel);
			String helpString = "Single click for spectrum and power vs. time plots.\n"
					+ "Mouse, drag and release to move time window.\n"
					+ "Double click for daily report.";

			spectrogramPanel.setTitle(helpString);
			spectrumAndOccupancyPanel = new VerticalPanel();
			spectrumAndOccupancyPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			vpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			vpanel.add(spectrumAndOccupancyPanel);

		} catch (Throwable ex) {
			ex.printStackTrace();
			logger.log(Level.SEVERE, ex.getMessage());
		}
	}

	/**
	 * Gets called after the spectrogram has loaded from the server. Also gets
	 * called when we want to redraw the spectrogram.
	 * 
	 */
	public void handleSpectrogramLoadEvent() {
		RootPanel.get().remove(image);

		image.setVisible(true);

		ImageElement imageElement = ImageElement.as(image.getElement());

		Canvas canvas = Canvas.createIfSupported();
		if (surface != null) {
			spectrogramPanel.remove(surface);
			spectrogramPanel.remove(xaxisPanel);
		}
		surface = canvas;

		surface.setWidth(canvasPixelWidth + "px");
		// The following is needed for IE but screws up for chrome or firefox.
		// (why?)
		String platform = Window.Navigator.getAppName();
		if (platform.equals("Microsoft Internet Explorer")) {
			surface.setHeight(canvasPixelHeight + "px");
		}
		surface.addMouseMoveHandler(new SurfaceMouseMoveHandlerImpl());

		surface.getContext2d().drawImage(imageElement, 0, 0);
		spectrogramPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		spectrogramPanel.setHeight(canvasPixelHeight + "px");
		spectrogramPanel.add(surface);
		spectrogramPanel.add(xaxisPanel);

		freqPanel.setHeight(canvasPixelHeight + "px");
		logger.log(Level.FINER, "Image Height " + canvasPixelHeight);

		yPixelsPerMegahertz = (double) (canvasPixelHeight)
				/ (double) (maxFreq - minFreq);
		logger.finer("yPixelsPerMegaherz = " + yPixelsPerMegahertz
				+ "canvasPixelHeight " + canvasPixelHeight);

		surface.addMouseDownHandler(new MouseDownHandler() {

			@Override
			public void onMouseDown(MouseDownEvent mouseDownEvent) {
				logger.finer("mouseDownEvent");
				mouseDownTime = System.currentTimeMillis();
				mouseDownPosition = mouseDownEvent.getX();

			}
		});

		surface.addMouseUpHandler(new MouseUpHandler() {

			@Override
			public void onMouseUp(MouseUpEvent mouseUpEvent) {
				logger.finer("onMouseUp");
				long uptime = System.currentTimeMillis();
				if (uptime - mouseDownTime > 500) {
					// Detected a drag.
					int mouseUpPosition = mouseUpEvent.getX();
					int movement = mouseUpPosition - mouseDownPosition;
					double time = movement / getxPixelsPerMilisecond();
					spectrogramDragHandler.drag((long) time);

				} else {
					if (timer == null) {
						clickCounter = 1;
						timer = new Timer() {

							@Override
							public void run() {
								if (clickCounter >= 2) {
									logger.finest("Double Click detected");
									long dayBoundary = currentTime
											/ MILISECONDS_PER_DAY
											* MILISECONDS_PER_DAY;

									DailyReport dailyReport = new DailyReport(
											spectrumBrowser, spectrogram,
											spectrumLocationSelection,
											rootVerticalPanel, sessionId,
											dayBoundary, minTime, maxTime,
											minFreq, maxFreq, minPower,
											canvasPixelWidth, canvasPixelHeight);
									dailyReport.draw();
								} else {
									logger.finest("Single click");
									SpectrogramFragment.this
											.drawOccupancyAndSpectrum();
								}
								timer = null;
								clickCounter = 0;

							}
						};
						timer.schedule(600);
					} else {
						clickCounter++;
					}
				}
			}
		});
		if (cmapUrl != null) {
			ImagePreloader.load(cmapUrl, new ImageLoadHandler() {

				@Override
				public void imageLoaded(ImageLoadEvent event) {
					FitImage image = new FitImage();
					// TODO -- make this width part of CSS
					image.setFixedWidth(30);
					image.setUrl(event.getImageUrl());
					ImageElement imageElement = ImageElement.as(image
							.getElement());
					imageElement.setAttribute("HEIGHT", canvasPixelHeight
							+ "px");

					image.setVisible(true);
					if (powerMapImage != null) {
						powerMapPanel.remove(powerMapImage);

					}
					powerMapPanel.add(image);
					powerMapImage = image;
					powerMapPanel.setHeight(canvasPixelHeight + "px");

				}
			});
		}

	}

	public void setSpectrogramImage(String url, String cmapUrl) {
		try {

			this.cmapUrl = cmapUrl;
			SpectrogramFragment.this.image = new FitImage();
			image.setWidth(canvasPixelWidth + "px");
			// image.setFixedWidth(canvasPixelWidth);
			image.addLoadHandler(new LoadHandler() {

				@Override
				public void onLoad(LoadEvent event) {

					logger.fine("Image loaded");
					handleSpectrogramLoadEvent();

				}
			});
			image.setVisible(false);

			ImageElement imageElement = ImageElement.as(image.getElement());
			imageElement.setAttribute("HEIGHT", canvasPixelHeight + "px");
			image.setHeight(canvasPixelHeight + "px");

			logger.log(Level.FINER, "Setting URL " + url);
			image.addErrorHandler(new ErrorHandler() {

				@Override
				public void onError(ErrorEvent event) {
					logger.log(Level.SEVERE, "Error loading image");
					Window.alert("Error loading image");

				}
			});

			image.setUrl(url);
			RootPanel.get().add(image);

		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error retrieving image", ex);
		}
	}

	public void addOccupancyMinPowerPanel(VerticalPanel occupancyMinPowerVpanel) {
		this.verticalOccupancySelector = occupancyMinPowerVpanel;
		hpanel.add(verticalOccupancySelector);

	}

	private double getxPixelsPerMilisecond() {
		return (double) ((double) (canvasPixelWidth) / (double) (maxTime - minTime));
	}

	public void setMinMaxDates(long minDate, long maxDate) {
		this.minTime = minDate;
		this.maxTime = maxDate;
	}

	
}
