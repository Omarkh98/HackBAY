// BadCode.java
import java.util.ArrayList;
import java.util.List;
import java.util.Date; // Unused import

public class BadCode {

    private String unusedField; // Potentially unused field

    // Method with too many parameters
    public void overlyComplexMethod(int a, int b, int c, int d, int e, int f, String g, boolean h) {
        System.out.println("This method has many parameters: " + a + b + c + d + e + f + g + h); // System.out usage

        int x = 10; // Unused local variable
        String message = "";

        // Inefficient string concatenation in a loop
        for (int i = 0; i < 10; i++) {
            message += " " + i; // Bad practice
        }
        System.out.println(message);

        if (a > b && b > c && c > d && d > e && e > f) { // High cyclomatic complexity (simplified here)
            System.out.println("Complex condition");
        } else if (a < b || b < c || c < d || d < e || e < f) {
            System.out.println("Another complex condition");
        } else {
            try {
                // Potentially problematic operation
                int result = a / (b - c); // Potential division by zero, not directly a PMD style issue but can be flagged
                System.out.println("Result: " + result);
            } catch (ArithmeticException ex) {
                // Empty catch block - bad practice!
            } catch (Exception ex) {
                System.err.println("Some other error: " + ex.getMessage()); // Using System.err is fine, but the previous catch is empty
            }
        }
    }

    public void anotherMethod() {
        List<String> items = new ArrayList<>();
        if (items.isEmpty()) { // Can be simplified by some rules
            System.out.println("List is empty");
        }

        // Example of a magic number
        if (items.size() > 5) {
            System.out.println("More than 5 items");
        }
    }

    // Potentially unused private method
    private void utilityMethod() {
        System.out.println("This might be unused.");
    }

    public static void main(String[] args) {
        BadCode bc = new BadCode();
        bc.overlyComplexMethod(1, 2, 3, 4, 5, 6, "test", true);
        bc.overlyComplexMethod(6, 5, 4, 3, 2, 1, "another test", false);
        bc.anotherMethod();
    }
}
