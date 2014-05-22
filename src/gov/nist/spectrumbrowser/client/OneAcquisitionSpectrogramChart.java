package gov.nist.spectrumbrowser.client;



import java.util.ArrayList;
import java.util.Date;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.canvas.client.Canvas;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.dev.json.JsonObject;
import com.google.gwt.dom.client.ImageElement;
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
import com.google.gwt.i18n.client.DateTimeFormat;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Timer;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.kiouri.sliderbar.client.event.BarValueChangedEvent;
import com.kiouri.sliderbar.client.event.BarValueChangedHandler;
import com.kiouri.sliderbar.client.solution.simplevertical.SliderBarSimpleVertical;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.reveregroup.gwt.imagepreloader.ImageLoadEvent;
import com.reveregroup.gwt.imagepreloader.ImageLoadHandler;
import com.reveregroup.gwt.imagepreloader.ImagePreloader;

public class OneAcquisitionSpectrogramChart implements
		SpectrumBrowserCallback<String> {
	String mSensorId;
	String mTitle;
	SpectrumBrowser mSpectrumBrowser;
	long mSelectionTime;
	SpectrumBrowserShowDatasets mSpectrumBrowserShowDatasets;
	DailyStatsChart mDailyStatsChart;
	OneDayOccupancyChart mOneDayOccupancyChart;
	int mWidth;
	int mHeight;
	JSONValue jsonValue;
	public static final long MILISECONDS_PER_DAY = 24 * 60 * 60 * 1000;
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
	int timeDelta;
	private double yPixelsPerMegahertz;
	private int canvasPixelWidth;
	private int canvasPixelHeight;
	private Label maxPowerLabel;
	private Label minPowerLabel;
	private SpectrumBrowser spectrumBrowser;
	private StatisticsChart spectrumChart;
	private StatisticsChart occupancyChart;
	private VerticalPanel spectrogramPanel;
	private VerticalPanel freqPanel;
	private HorizontalPanel powerMapPanel;
	private Canvas spectrogramCanvas;
	private HorizontalPanel xaxisPanel;
	private VerticalPanel verticalOccupancySelector;
	private FitImage powerMapImage;
	private Image spectrogramImage;
	private long localTimeOfAcquisition;
	private String localDateOfAcquisition;
	private String cmapUrl;
	private String spectrogramUrl;
	private String occupancyUrl;
	private FitImage occupancyImage;
	VerticalPanel occupancyPanel;
	private SliderBarSimpleVertical occupancyMinPowerSliderBar;
	private Label occupancyMinPowerLabel;
	private String mTimeZoneId;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

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

			currentFreq = (long) ((maxFreq - minFreq) * yratio) + minFreq;
			currentTime = (long) ((maxTime - minTime) * xratio) + minTime;
			currentValue.setText("Time = " + currentTime + " seconds; Freq = "
					+ currentFreq + " MHz");
		}

	}

	public class OccupancyMinPowerSliderHandler implements
			BarValueChangedHandler {
		Label occupancyMinPowerLabel;

		public OccupancyMinPowerSliderHandler(Label occupancyMinPowerLabel) {
			occupancyMinPowerSliderBar.setValue(100);
			this.occupancyMinPowerLabel = occupancyMinPowerLabel;
			occupancyMinPowerLabel.setText(minPower + " dBm");
			this.occupancyMinPowerLabel
					.setTitle("Power Cutoff for Occupancy Graph");
		}

		@Override
		public void onBarValueChanged(BarValueChangedEvent event) {
			try {

				int occupancyBarValue = occupancyMinPowerSliderBar.getValue();
				logger.log(Level.FINEST, "bar value changed new value is "
						+ occupancyBarValue);
				occupancyMinPower = (int) ((1 - (double) occupancyBarValue / 100.0)
						* (maxPower - minPower) + minPower);
				occupancyMinPowerLabel.setText(Integer
						.toString((int) occupancyMinPower) + " dBm");

			} catch (Exception ex) {
				logger.log(Level.SEVERE, " Exception ", ex);
			}

		}

	}

	public OneAcquisitionSpectrogramChart(String sensorId, long selectionTime,
			String title,  VerticalPanel verticalPanel,
			SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			DailyStatsChart dailyStatsChart,
			OneDayOccupancyChart oneDayOccupancyChart, int width, int height) {
		mSensorId = sensorId;
		mSelectionTime = selectionTime;
		mTitle = title;
		vpanel = verticalPanel;
		mSpectrumBrowser = spectrumBrowser;
		mSpectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		mDailyStatsChart = dailyStatsChart;
		mOneDayOccupancyChart = oneDayOccupancyChart;
		mWidth = 600;
		mHeight = 400;

		mSpectrumBrowser.getSpectrumBrowserService()
				.generateSingleAcquisitionSpectrogramAndPowerVsTimePlot(
						mSpectrumBrowser.getSessionId(), sensorId,
						mSelectionTime, mWidth, mHeight, this);

	}
	
	

	@Override
	public void onSuccess(String result) {
		try {
			logger.finer("result = " + result);
			jsonValue = JSONParser.parseLenient(result);
			timeDelta = (int) jsonValue.isObject().get("timeDelta").isNumber()
					.doubleValue();
			String spectrogramFile = jsonValue.isObject().get("spectrogram")
					.isString().stringValue();
			String colorBarFile = jsonValue.isObject().get("cbar").isString()
					.stringValue();
			String occupancyFile = jsonValue.isObject().get("occupancy")
					.isString().stringValue();
			occupancyUrl = SpectrumBrowser.getGeneratedDataPath()
					+ occupancyFile;
			spectrogramUrl = SpectrumBrowser.getGeneratedDataPath()
					+ spectrogramFile;
			cmapUrl = SpectrumBrowser.getGeneratedDataPath() + colorBarFile;
			maxPower = (int) jsonValue.isObject().get("maxPower").isNumber()
					.doubleValue();
			minPower = (int) jsonValue.isObject().get("minPower").isNumber()
					.doubleValue();
			minFreq = (int) jsonValue.isObject().get("minFreq").isNumber()
					.doubleValue() / 1000;
			maxFreq = (int) jsonValue.isObject().get("maxFreq").isNumber()
					.doubleValue() / 1000;
			localTimeOfAcquisition = (int) jsonValue.isObject()
					.get("tStartLocalTime").isNumber().doubleValue();
			Date newValue = new Date(localTimeOfAcquisition * 1000);
			DateTimeFormat dateTimeFormat = DateTimeFormat
					.getFormat("yyyy-MM-dd HH:mm:ss");
			String timeZone = jsonValue.isObject().get("timeZone").isString()
					.stringValue();
			localDateOfAcquisition = dateTimeFormat.format(newValue) + " "
					+ timeZone;
			minTime = 0;
			maxTime = minTime + timeDelta;
			draw();
		} catch (Throwable throwable) {
			logger.log(Level.SEVERE, "Error parsing json result from server",
					throwable);
			mSpectrumBrowser.displayError("Error parsing JSON");
		}

	}

	private void drawNavigation() {
		MenuBar menuBar = new MenuBar();
		SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();

		menuBar.addItem(safeHtml.appendEscaped("Log Off").toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						spectrumBrowser.logoff();

					}
				});

		menuBar.addItem(new SafeHtmlBuilder().appendEscaped("Select Data Set")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				mSpectrumBrowserShowDatasets.buildUi();
			}
		});

		menuBar.addItem(new SafeHtmlBuilder().appendEscaped("Daily Statistics")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				mDailyStatsChart.draw();
			}
		});

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped("One Day Statistics")
						.toSafeHtml(), new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						mOneDayOccupancyChart.draw();

					}
				});

		menuBar.addItem(new SafeHtmlBuilder().appendEscaped("About")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {

			}
		});

		menuBar.addItem(new SafeHtmlBuilder().appendEscaped("Help")
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				// TODO Auto-generated method stub

			}
		});
		vpanel.add(menuBar);
		HTML title = new HTML("<H1>Acquistion Start : "
				+ localDateOfAcquisition + " </H1>");
		vpanel.add(title);

	}

	/**
	 * Gets called after the spectrogram has loaded from the server. Also gets
	 * called when we want to redraw the spectrogram.
	 * 
	 */
	public void handleSpectrogramLoadEvent() {
		RootPanel.get().remove(spectrogramImage);

		spectrogramImage.setVisible(true);

		ImageElement imageElement = ImageElement.as(spectrogramImage
				.getElement());

		Canvas canvas = Canvas.createIfSupported();
		if (spectrogramCanvas != null) {
			spectrogramPanel.remove(spectrogramCanvas);
			spectrogramPanel.remove(xaxisPanel);
		}
		spectrogramCanvas = canvas;

		spectrogramCanvas.setWidth(canvasPixelWidth + "px");
		spectrogramCanvas.setHeight(canvasPixelHeight + "px");
		spectrogramCanvas
				.addMouseMoveHandler(new SurfaceMouseMoveHandlerImpl());

		spectrogramCanvas.getContext2d().drawImage(imageElement, 0, 0);
		spectrogramCanvas.getContext2d().rect(0, 0, canvasPixelWidth,
				canvasPixelHeight);
		spectrogramPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		spectrogramPanel.clear();
		spectrogramPanel.setHeight(canvasPixelHeight + "px");
		spectrogramPanel.add(spectrogramCanvas);
		spectrogramPanel.add(xaxisPanel);

		freqPanel.setHeight(canvasPixelHeight + "px");
		logger.log(Level.FINER, "Image Height " + canvasPixelHeight);

		yPixelsPerMegahertz = (double) (canvasPixelHeight)
				/ (double) (maxFreq - minFreq);
		logger.finer("yPixelsPerMegaherz = " + yPixelsPerMegahertz
				+ "canvasPixelHeight " + canvasPixelHeight);

		if (cmapUrl != null) {
			ImagePreloader.load(cmapUrl, new ImageLoadHandler() {

				@Override
				public void imageLoaded(ImageLoadEvent event) {
					FitImage image = new FitImage();
					// TODO -- make this width part of CSS
					image.setFixedWidth(30);
					image.setHeight(canvasPixelHeight + "px");
					image.setUrl(event.getImageUrl());
					image.setPixelSize(30, canvasPixelHeight);
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

	private void handleOccupancyImageLoadEvent() {
		RootPanel.get().remove(occupancyImage);
		occupancyImage.setPixelSize(canvasPixelWidth, canvasPixelHeight);
		occupancyImage.setVisible(true);
		occupancyPanel.add(occupancyImage);

	}

	private void setSpectrogramImage() {
		try {

			spectrogramImage = new FitImage();
			spectrogramImage.setWidth(canvasPixelWidth + "px");
			spectrogramImage.setPixelSize(canvasPixelWidth, canvasPixelHeight);
			// image.setFixedWidth(canvasPixelWidth);
			spectrogramImage.addLoadHandler(new LoadHandler() {

				@Override
				public void onLoad(LoadEvent event) {

					logger.fine("Image loaded");
					handleSpectrogramLoadEvent();

				}
			});
			spectrogramImage.setVisible(false);

			ImageElement imageElement = ImageElement.as(spectrogramImage
					.getElement());
			imageElement.setAttribute("HEIGHT", canvasPixelHeight + "px");
			spectrogramImage.setHeight(canvasPixelHeight + "px");

			logger.log(Level.FINER, "Setting URL " + spectrogramUrl);
			spectrogramImage.addErrorHandler(new ErrorHandler() {

				@Override
				public void onError(ErrorEvent event) {
					logger.log(Level.SEVERE, "Error loading image");
					Window.alert("Error loading image");

				}
			});

			spectrogramImage.setUrl(spectrogramUrl);
			RootPanel.get().add(spectrogramImage);

			occupancyImage = new FitImage();
			occupancyImage.setWidth(canvasPixelWidth + "px");
			occupancyImage.setPixelSize(canvasPixelWidth, canvasPixelHeight);
			// image.setFixedWidth(canvasPixelWidth);
			occupancyImage.addLoadHandler(new LoadHandler() {

				@Override
				public void onLoad(LoadEvent event) {

					logger.fine("Image loaded");
					handleOccupancyImageLoadEvent();

				}
			});
			occupancyImage.setVisible(false);
			occupancyImage.setUrl(occupancyUrl);
			RootPanel.get().add(occupancyImage);

		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error retrieving image", ex);
		}
	}

	private void draw() {
		vpanel.clear();
		drawNavigation();
		hpanel = new HorizontalPanel();

		hpanel.setSpacing(10);
		hpanel.setWidth(mWidth + "px");
		hpanel.setHeight(mHeight + "px");
		hpanel.setStyleName("spectrogram");
		canvasPixelWidth = mWidth;
		canvasPixelHeight = mHeight;
		xaxisPanel = new HorizontalPanel();
		xaxisPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
		HorizontalPanel xaxis = new HorizontalPanel();
		xaxis.setWidth(canvasPixelWidth + 30 + "px");
		xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
		xaxis.add(new Label("0"));
		xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		xaxis.add(new Label("Time (seconds)"));
		xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
		xaxis.add(new Label(Double.toString(timeDelta)));
		xaxisPanel.add(xaxis);

		// Attach the labels for the spectrogram power
		VerticalPanel powerLevelPanel = new VerticalPanel();
		powerLevelPanel.setWidth(100 + "px");
		this.maxPowerLabel = new Label();
		this.minPowerLabel = new Label();
		powerLevelPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
		powerLevelPanel.add(maxPowerLabel);
		powerLevelPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
		powerLevelPanel.add(new Label("Power (dBm) "));
		powerLevelPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
		powerLevelPanel.add(minPowerLabel);
		// Attach labels for the frequency.
		freqPanel = new VerticalPanel();
		freqPanel.setWidth(100 + "px");
		powerLevelPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
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
		currentValue = new Label(
				"Click on spectrogram for Spectrum and Occupancy");
		vpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		vpanel.add(currentValue);
		vpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
		vpanel.add(hpanel);
		String helpString = "Single click for spectrum plot.";

		VerticalPanel occupancyMinPowerVpanel = new VerticalPanel();
		this.occupancyMinPowerSliderBar = new SliderBarSimpleVertical(100,
				mHeight + "px", true);
		occupancyMinPowerVpanel.add(occupancyMinPowerSliderBar);
		occupancyMinPowerSliderBar.setMaxValue(100);
		occupancyMinPowerVpanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
		occupancyMinPowerVpanel
				.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
		this.occupancyMinPowerLabel = new Label();
		occupancyMinPowerVpanel.add(occupancyMinPowerLabel);
		Button generateSpectrogramButton = new Button("Cutoff and Redraw");
		occupancyMinPowerVpanel.add(generateSpectrogramButton);
		generateSpectrogramButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				mSpectrumBrowser.getSpectrumBrowserService()
					.generateSingleAcquisitionSpectrogramAndPowerVsTimePlot(
						mSpectrumBrowser.getSessionId(), mSensorId,
						mSelectionTime, occupancyMinPower, mWidth, mHeight, OneAcquisitionSpectrogramChart.this);
				
			}} );
		occupancyMinPowerSliderBar
				.addBarValueChangedHandler(new OccupancyMinPowerSliderHandler(
						occupancyMinPowerLabel));
		occupancyMinPowerSliderBar.setValue(100);
		hpanel.add(occupancyMinPowerVpanel);

		spectrogramPanel.setTitle(helpString);
		spectrumAndOccupancyPanel = new VerticalPanel();
		spectrumAndOccupancyPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		vpanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		vpanel.add(spectrumAndOccupancyPanel);

		occupancyPanel = new VerticalPanel();
		vpanel.add(occupancyPanel);

		setSpectrogramImage();
	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE, "Error communicating with server", throwable);
		mSpectrumBrowser.displayError("Error communicating with server");
	}

}
