package pymontecarlo.input.nistmonte;

import gov.nist.microanalysis.EPQLibrary.EPQException;
import gov.nist.microanalysis.NISTMonte.MonteCarloSS;
import gov.nist.microanalysis.Utility.Histogram;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Properties;

import ptpshared.io.CSVWriter;

/**
 * Abstract detector to collect data in a number of channels between two limits.
 * 
 * @author ppinard
 */
public abstract class AbstractChannelDetector extends
        AbstractScatteringDetector implements ChannelDetector {

    /** Histogram to store the data. */
    protected final Histogram histogram;



    /**
     * Creates a new <code>AbstractChannelDetector</code>.
     * 
     * @param min
     *            lower limit of the detector
     * @param max
     *            upper limit of the detector
     * @param channels
     *            number of channels (bins)
     */
    public AbstractChannelDetector(double min, double max, int channels) {
        if (channels <= 0)
            throw new IllegalArgumentException(
                    "Number of channels must be greater than 0");

        min = Math.min(min, max);
        max = Math.max(min, max);
        histogram = new Histogram(min, max, channels);
    }



    @Override
    public void setup(MonteCarloSS mcss) throws EPQException {
        mcss.addActionListener(this);
    }



    /**
     * Returns the header of the bins column.
     * 
     * @return header of the bins column
     */
    public abstract String getBinsHeader();



    /**
     * Returns the header of the counts column.
     * 
     * @return header of the counts column
     */
    public String getCountsHeader() {
        return "Counts";
    }



    @Override
    public void saveResults(File resultsDir, String baseName)
            throws IOException {
        File resultsFile = new File(resultsDir, baseName + ".csv");

        CSVWriter writer = new CSVWriter(new FileWriter(resultsFile));

        writer.writeNext(getBinsHeader(), getCountsHeader());

        double x, y;
        for (int i = 0; i < histogram.binCount(); i++) {
            x = (histogram.minValue(i) + histogram.maxValue(i)) / 2.0;
            y = histogram.counts(i);

            writer.writeNext(x, y);
        }

        writer.close();
    }



    @Override
    protected void saveAsProperties(Properties props) {
        super.saveAsProperties(props);

        props.setProperty("histogram.min", Double.toString(getMinimumLimit()));
        props.setProperty("histogram.max", Double.toString(getMaximumLimit()));
        props.setProperty("histogram.channels",
                Integer.toString(histogram.binCount()));
    }



    @Override
    public double getMinimumLimit() {
        return histogram.minValue(0);
    }



    @Override
    public double getMaximumLimit() {
        return histogram.maxValue(histogram.binCount() - 1);
    }



    @Override
    public double getChannelWidth() {
        return histogram.maxValue(0) - histogram.minValue(0);
    }



    @Override
    public int getChannels() {
        return histogram.binCount();
    }

}
