import { Link } from "react-router-dom";

const NotFound = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50">
      <h1 className="text-5xl font-bold">404</h1>

      <p className="mt-2 text-gray-500">
        Page not found
      </p>

      <Link
        to="/"
        className="mt-4 rounded bg-green-600 px-4 py-2 text-white"
      >
        Go Home
      </Link>
    </div>
  );
};

export default NotFound;